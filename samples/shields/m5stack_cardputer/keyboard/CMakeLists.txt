# Copyright (c) 2024 Benjamin Cabé <benjamin@zephyrproject.org>
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)

set(SHIELD m5stack_cardputer)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(m5stack_cardputer_keyboard)
target_sources(app PRIVATE src/main.c)
