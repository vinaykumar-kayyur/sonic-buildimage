/*
 * dx010-gpio.c - Kernel module for Seastone DX010 gpios.
 *
 * Copyright (C) 2018 Celestica Corp.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include <linux/module.h>
#include <linux/gpio.h>
#include <linux/kernel.h>
#include <linux/err.h>
#include <linux/printk.h>

#define MODULE_NAME "dx010-gpio"

#define NUM_FAN 5
#define NUM_PSU 2
#define UPDATE_MS 100
#define CHECK_MS 1000
#define CHECK_COUNTER  CHECK_MS/UPDATE_MS


struct fan_gpio {
    unsigned char presence_pin;
    unsigned char red_led_pin;
    unsigned char yel_led_pin;
    int prs;
};

struct psu_gpio {
    unsigned char absence_pin;
    unsigned char powerok_pin;
};

static struct gpio_chip *gc;
static struct fan_gpio fan_gpios[NUM_FAN] = {
  {.presence_pin = 10,
   .red_led_pin = 29,
   .yel_led_pin = 30,
   .prs = 1
  },
  {.presence_pin = 11,
   .red_led_pin = 31,
   .yel_led_pin = 32,
   .prs = 1
  },
  {.presence_pin = 12,
   .red_led_pin = 33,
   .yel_led_pin = 34,
   .prs = 1
  },
  {.presence_pin = 13,
   .red_led_pin = 35,
   .yel_led_pin = 36,
   .prs = 1
  },
  {.presence_pin = 14,
   .red_led_pin = 37,
   .yel_led_pin = 38,
   .prs = 1
  }
};

static struct psu_gpio psu_gpios[NUM_PSU] = {
  {.absence_pin = 27,
   .powerok_pin = 22
  },
  {.absence_pin = 28,
   .powerok_pin = 25,
  }
};

static int chip_match_name(struct gpio_chip *chip, void *data){
  return !strcmp(chip->label, data);
}

static void init_fan_gpio(void){
  int index;
  for( index=0; index < NUM_FAN; index++){
    gpio_request(gc->base+fan_gpios[index].presence_pin, NULL);
    gpio_request(gc->base+fan_gpios[index].red_led_pin, NULL);
    gpio_request(gc->base+fan_gpios[index].yel_led_pin, NULL);
    gpio_direction_input(gc->base+fan_gpios[index].presence_pin);
    gpio_direction_output(gc->base+fan_gpios[index].red_led_pin, 1);
    gpio_direction_output(gc->base+fan_gpios[index].yel_led_pin, 0);
    gpio_export(gc->base+fan_gpios[index].presence_pin,0);
    gpio_export(gc->base+fan_gpios[index].red_led_pin,0);
    gpio_export(gc->base+fan_gpios[index].yel_led_pin,0);
  }
}

static void init_psu_gpio(void){
  int index;
  for( index=0; index < NUM_PSU; index++){
    gpio_request(gc->base+psu_gpios[index].absence_pin, NULL);
    gpio_request(gc->base+psu_gpios[index].powerok_pin, NULL);
    gpio_direction_input(gc->base+psu_gpios[index].absence_pin);
    gpio_direction_input(gc->base+psu_gpios[index].powerok_pin);
    gpio_export(gc->base+psu_gpios[index].absence_pin,0);
    gpio_export(gc->base+psu_gpios[index].powerok_pin,0);
  }
}

static void deinit_fan_gpio(void){
  int index;
  for( index=0; index < NUM_PSU; index++){
    gpio_unexport(gc->base+fan_gpios[index].presence_pin);
    gpio_unexport(gc->base+fan_gpios[index].red_led_pin);
    gpio_unexport(gc->base+fan_gpios[index].yel_led_pin);
    gpio_free(gc->base+fan_gpios[index].presence_pin);
    gpio_free(gc->base+fan_gpios[index].red_led_pin);
    gpio_free(gc->base+fan_gpios[index].yel_led_pin);
  }
}

static void deinit_psu_gpio(void){
  int index;
  for( index=0; index < NUM_PSU; index++){
    gpio_unexport(gc->base+psu_gpios[index].absence_pin);
    gpio_unexport(gc->base+psu_gpios[index].powerok_pin);
    gpio_free(gc->base+psu_gpios[index].absence_pin);
    gpio_free(gc->base+psu_gpios[index].powerok_pin);
  }
}

static int __init dx010_gpio_init(void){


  struct gpio_chip *find;
  gc = NULL;  
  find = gpiochip_find("pca9505", chip_match_name);
  if(!find){
    printk(KERN_ERR "DX010 GPIO Chip not found!");
    return -ENODEV;
  }
  gc = find;
  init_fan_gpio();
  init_psu_gpio();
  return 0;
}

static void __exit dx010_gpio_exit(void){
  deinit_fan_gpio();
  deinit_psu_gpio();
  gc = NULL;
}

module_init(dx010_gpio_init);
module_exit(dx010_gpio_exit);


MODULE_LICENSE("GPL");
MODULE_AUTHOR("Celestica Inc.");
MODULE_DESCRIPTION("DX010 gpio driver");