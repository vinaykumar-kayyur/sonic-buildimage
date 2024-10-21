/*
 * Copyright(C) 2001-2015s whitebox Network. All rights reserved.
 */
/*
 * dfd_cfg_file.c
 * Original Author: sonic_rd@whitebox 2020-02-17
 *
 * Kernel module file operation: Read files into memory at one time. Multi-threading is not supported
 *
 * History
 *  [Version]        [Author]                   [Date]            [Description]
 *     v1.0    sonic_rd@whitebox         2020-02-17        Initial version
 *
 */

#include <asm/unistd.h>
#include <asm/uaccess.h>
#include <linux/stat.h>
#include <linux/slab.h>
#include <linux/fs.h>
#include <linux/mm.h>
#include <linux/types.h>
#include <linux/module.h>
#include <linux/kernel.h>

#include "../include/dfd_cfg_file.h"
#include "../include/wb_module.h"

struct getdents_callback {
    struct dir_context ctx;
    const char *obj_name;    /* Name to be matched */
    char *match_name;        /* Matching result */
    int dir_len;             /* Directory name length */
    int found;               /* Configuration flag */
};

/*
 * Open file
 * @fname: filename
 * @kfile_ctrl: File control variable
 *
 * @returns: 0 Success, other failure
 */
int kfile_open(char *fname, kfile_ctrl_t *kfile_ctrl)
{
    int ret;
    struct file *filp;
    loff_t pos;

    if ((fname == NULL) || (kfile_ctrl == NULL)) {
        return KFILE_RV_INPUT_ERR;
    }

    /* Open file */
    filp = filp_open(fname, O_RDONLY, 0);
    if (IS_ERR(filp)) {
        return KFILE_RV_OPEN_FAIL;
    }

    kfile_ctrl->size = filp->f_inode->i_size;

    /* Request file size memory */
    kfile_ctrl->buf = kmalloc(kfile_ctrl->size, GFP_KERNEL);
    if (kfile_ctrl->buf == NULL) {
        ret = KFILE_RV_MALLOC_FAIL;
        goto close_fp;
    }
    memset(kfile_ctrl->buf, 0, kfile_ctrl->size);
    /* Read file contents */
    pos = 0;
    ret = kernel_read(filp, kfile_ctrl->buf, kfile_ctrl->size, &pos);
    if (ret < 0) {
        ret = KFILE_RV_RD_FAIL;
        goto free_buf;
    }
    /* Set current position */
    kfile_ctrl->pos = 0;

    ret = KFILE_RV_OK;
    goto close_fp;

free_buf:
    kfree(kfile_ctrl->buf);
    kfile_ctrl->buf = NULL;

close_fp:
    filp_close(filp, NULL);
    return ret;
}

/*
 * Close file
 * @kfile_ctrl: File control variable
 */
void kfile_close(kfile_ctrl_t *kfile_ctrl)
{
    if (kfile_ctrl == NULL) {
        return;
    }

    /* Set the file size to 0 to free memory */
    kfile_ctrl->size = 0;
    kfile_ctrl->pos = 0;
    if (kfile_ctrl->buf) {
        kfree(kfile_ctrl->buf);
        kfile_ctrl->buf = NULL;
    }
}

/*
 * Get a row
 * @buf: buf Buffer area
 * @buf_size: buf size
 * @kfile_ctrl: File control variable
 *
 * @returns: >=0 Success, other failure
 */
int kfile_gets(char *buf, int buf_size, kfile_ctrl_t *kfile_ctrl)
{
    int i;
    int has_cr = 0;

    if ((buf == NULL) || (buf_size <= 0) || (kfile_ctrl == NULL) || (kfile_ctrl->buf == NULL)
            || (kfile_ctrl->size <= 0)) {
        return KFILE_RV_INPUT_ERR;
    }

    /* Clear the buf first */
    memset(buf, 0, buf_size);
    for (i = 0; i < buf_size; i++) {
        /* It's at the end of the file */
        if (kfile_ctrl->pos >= kfile_ctrl->size) {
            break;
        }

        /* The previous data is a newline character, and a line has been copied */
        if (has_cr) {
            break;
        }

        /* Search for a newline */
        if (IS_CR(kfile_ctrl->buf[kfile_ctrl->pos])) {
            has_cr = 1;
        }

        /* Copy data */
        buf[i] = kfile_ctrl->buf[kfile_ctrl->pos];
        kfile_ctrl->pos++;
    }

    return i;
}

/*
 * Read data
 * @buf: buf Buffer area
 * @buf_size: buf size
 * @kfile_ctrl: File control variable
 *
 * @returns: >=0 Success, other failure
 */
int kfile_read(int32_t addr, char *buf, int buf_size, kfile_ctrl_t *kfile_ctrl)
{
    int i;

    if ((buf == NULL) || (buf_size <= 0) || (kfile_ctrl == NULL) || (kfile_ctrl->buf == NULL)
            || (kfile_ctrl->size <= 0)) {
        return KFILE_RV_INPUT_ERR;
    }

    /* Address check */
    if ((addr < 0) || (addr >= kfile_ctrl->size)) {
        return KFILE_RV_ADDR_ERR;
    }

    /* Clear the buf first */
    memset(buf, 0, buf_size);

    kfile_ctrl->pos = addr;
    for (i = 0; i < buf_size; i++) {
        /* It's at the end of the file */
        if (kfile_ctrl->pos >= kfile_ctrl->size) {
            break;
        }

        /* Copy data */
        buf[i] = kfile_ctrl->buf[kfile_ctrl->pos];
        kfile_ctrl->pos++;
    }

    return i;
}

static int kfile_filldir_one(struct dir_context *ctx, const char * name, int len,
                             loff_t pos, u64 ino, unsigned int d_type)
{
    struct getdents_callback *buf;
    int result;
    buf = container_of(ctx, struct getdents_callback, ctx);
    result = 0;
    if (strncmp(buf->obj_name, name, strlen(buf->obj_name)) == 0) {
        if (buf->dir_len < len) {
            DBG_DEBUG(DBG_ERROR, "match ok. dir name:%s, but buf_len %d small than dir len %d.\n",
                name, buf->dir_len, len);
            buf->found = 0;
            return -1;
        }
        memset(buf->match_name, 0, buf->dir_len);
        memcpy(buf->match_name, name, len);
        buf->found = 1;
        result = -1;
    }
    return result;
}

/*
 * Read data
 * @buf: buf Buffer area
 * @buf_size: buf size
 * @kfile_ctrl: File control variable
 *
 * @returns: >=0 Success, other failure
 */
int kfile_iterate_dir(const char *dir_path, const char *obj_name, char *match_name, int len)
{
    int ret;
    struct file *dir;
    struct getdents_callback buffer = {
        .ctx.actor = kfile_filldir_one,
    };

    if (!dir_path || !obj_name || !match_name) {
        DBG_DEBUG(DBG_ERROR, "params error. \n");
        return KFILE_RV_INPUT_ERR;
    }
    buffer.obj_name = obj_name;
    buffer.match_name = match_name;
    buffer.dir_len = len;
    buffer.found = 0;
    /* Open folde */
    dir = filp_open(dir_path, O_RDONLY, 0);
    if (IS_ERR(dir)) {
        DBG_DEBUG(DBG_ERROR, "filp_open error, dir path:%s\n", dir_path);
        return KFILE_RV_OPEN_FAIL;
    }
    ret = iterate_dir(dir, &buffer.ctx);
    if (buffer.found) {
        DBG_DEBUG(DBG_VERBOSE, "match ok, dir name:%s\n", match_name);
        filp_close(dir, NULL);
        return DFD_RV_OK;
    }
    filp_close(dir, NULL);
    return -DFD_RV_NODE_FAIL;
}

#if 0
/*
 * Write data
 * @fname: indicates the file name
 * @addr: offset address of the file to be written
 * @buf: Writes data
 * @buf_size: indicates the data size
 *
 * @returns: >=0 Success, others fail
 */
int kfile_write(char *fpath, int32_t addr, char *buf, int buf_size)
{
    int ret = KFILE_RV_OK;
    struct file *filp;
    int wlen;

    if ((fpath == NULL) || (buf == NULL) || (buf_size <= 0)) {
        return KFILE_RV_INPUT_ERR;
    }

    /* Address check */
    if (addr < 0) {
        return KFILE_RV_ADDR_ERR;
    }

    /* Open file */
    filp = filp_open(fpath, O_RDWR, 0);
    if (IS_ERR(filp)) {
        return KFILE_RV_OPEN_FAIL;
    }

    filp->f_op->llseek(filp,0,0);
    filp->f_pos = addr;
    /* Write file content */
    wlen = filp->f_op->write(filp, buf, buf_size, &(filp->f_pos));
    if (wlen < 0) {
        ret = KFILE_RV_WR_FAIL;
    }

    filp->f_op->llseek(filp,0,0);
    filp_close(filp, NULL);

    return ret;
}
#endif
