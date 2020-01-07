/*!
 *  execute IPMI command and get result
 *
 *  @param netfn        [in]  code of network function
 *  @param cmd          [in]  code of command
 *  @param data         [in]  array of command data
 *  @param data_len     [in]  length of data
 *  @param result       [out] array of result
 *  @param result_len   [inout] in:  length of result array buffer
 *                              out: length of executed result
 *
 *  @return     0   successful
 *             -1   IPMI response failed
 *             -2   IPMI create user failed
 *             -3   IPMI request failed
 *             -4   IPMI response failed
 *
 *  @note       result and result_len do _NOT_ include the complete code.
 */
int ipmi_cmd(
    char    netfn,
    char    cmd,
    char    *data,
    int     data_len,
    char    *result,
    int     *result_len
);
