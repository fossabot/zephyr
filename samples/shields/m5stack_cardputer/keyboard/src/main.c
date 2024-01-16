/*
 * Copyright (c) 2012-2014 Wind River Systems, Inc.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <stdio.h>
#include <zephyr/input/input.h>

int main(void)
{
	return 0;
}

static void test_cb(struct input_event *evt)
{
	static int row, col, val;

	switch (evt->code) {
	case INPUT_ABS_X:
		col = evt->value;
		break;
	case INPUT_ABS_Y:
		row = evt->value;
		break;
	case INPUT_BTN_TOUCH:
		val = evt->value;
		break;
	}

	char keyboard_map[4][14] = {
		{'`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', '\b'},
		{'\t', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'},
		{'\0', '\0', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', '\n'},
		{'\0', '\0', '\0', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/'}};

	if (evt->sync && evt->value == 1) {
		// key down
		char key_pressed;
		int actual_row, actual_col;

		switch (col) {
		case 7:
			key_pressed = keyboard_map[0][row * 2];
			break;
		case 3:
			key_pressed = keyboard_map[0][1 + row * 2];
			break;
		case 6:
			key_pressed = keyboard_map[1][row * 2];
			break;
		case 2:
			key_pressed = keyboard_map[1][1 + row * 2];
			break;
		case 5:
			key_pressed = keyboard_map[2][row * 2];
			break;
		case 1:
			key_pressed = keyboard_map[2][1 + row * 2];
			break;
		case 4:
			key_pressed = keyboard_map[3][row * 2];
			break;
		case 0:
			key_pressed = keyboard_map[3][1 + row * 2];
			break;
		default:
			break;
		}

		printf("key pressed: %c\n", key_pressed);
	}
}
INPUT_CALLBACK_DEFINE(NULL, test_cb);
