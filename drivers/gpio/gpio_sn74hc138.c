/*
 * TODO add headers
 */

#define DT_DRV_COMPAT ti_sn74hc138

#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/gpio/gpio_utils.h>
#include <zephyr/sys/math_extras.h>

struct ti_sn74hc138_gpio_config {
	/* gpio_driver_config needs to be first */
	struct gpio_driver_config common;

	const struct gpio_dt_spec input_a_gpio;
	const struct gpio_dt_spec input_b_gpio;
	const struct gpio_dt_spec input_c_gpio;
};

struct ti_sn74hc138_gpio_data {
	/* gpio_driver_data needs to be first */
	struct gpio_driver_data common;
};

static int ti_sn74hc138_gpio_pin_configure(const struct device *port, gpio_pin_t pin,
					   gpio_flags_t flags)
{
	ARG_UNUSED(port);
	ARG_UNUSED(pin);
	ARG_UNUSED(flags);
	return 0;
}

static int ti_sn74hc138_gpio_port_get_raw(const struct device *port, gpio_port_value_t *value)
{
	return -ENOTSUP;
}

static int ti_sn74hc138_gpio_port_set_masked_raw(const struct device *port, gpio_port_pins_t mask,
						 gpio_port_value_t value)
{
	uint8_t idx = 0;
	const struct ti_sn74hc138_gpio_config *config = port->config;

	/* exactly one output can be selected at a time */
	if (POPCOUNT(value) != 1) {
		return -EINVAL;
	}

	idx = u32_count_trailing_zeros(value);

	gpio_pin_set_dt(&config->input_a_gpio, idx & 1);
	gpio_pin_set_dt(&config->input_b_gpio, (idx >> 1) & 1);
	gpio_pin_set_dt(&config->input_c_gpio, (idx >> 2) & 1);

	return 0;
}

static int ti_sn74hc138_gpio_port_set_bits_raw(const struct device *port, gpio_port_pins_t pins)
{
	return -ENOTSUP;
}

static int ti_sn74hc138_gpio_port_clear_bits_raw(const struct device *port, gpio_port_pins_t pins)
{
	return -ENOTSUP;
}

static int ti_sn74hc138_gpio_port_toggle_bits(const struct device *port, gpio_port_pins_t pins)
{
	return -ENOTSUP;
}

static int ti_sn74hc138_init(const struct device *port)
{
	int ret;
	const struct ti_sn74hc138_gpio_config *config = port->config;

	gpio_pin_configure_dt(&config->input_a_gpio, GPIO_OUTPUT_HIGH);
	gpio_pin_configure_dt(&config->input_b_gpio, GPIO_OUTPUT_HIGH);
	gpio_pin_configure_dt(&config->input_c_gpio, GPIO_OUTPUT_HIGH);

	return 0;
}

static const struct gpio_driver_api ti_sn74hc138_gpio_api = {
	.pin_configure = ti_sn74hc138_gpio_pin_configure,
	.port_get_raw = ti_sn74hc138_gpio_port_get_raw,
	.port_set_masked_raw = ti_sn74hc138_gpio_port_set_masked_raw,
	.port_set_bits_raw = ti_sn74hc138_gpio_port_set_bits_raw,
	.port_clear_bits_raw = ti_sn74hc138_gpio_port_clear_bits_raw,
	.port_toggle_bits = ti_sn74hc138_gpio_port_toggle_bits,
};

#define TI_SN74HC138_GPIO_INIT(n)                                                                  \
	static const struct ti_sn74hc138_gpio_config ti_sn74hc138_gpio_config_##n = {              \
		.common =                                                                          \
			{                                                                          \
				.port_pin_mask = GPIO_PORT_PIN_MASK_FROM_DT_INST(n),               \
			},                                                                         \
		.input_a_gpio = GPIO_DT_SPEC_INST_GET(0, input_a_gpios),                           \
		.input_b_gpio = GPIO_DT_SPEC_INST_GET(0, input_b_gpios),                           \
		.input_c_gpio = GPIO_DT_SPEC_INST_GET(0, input_c_gpios)};                          \
                                                                                                   \
	static struct ti_sn74hc138_gpio_data ti_sn74hc138_gpio_data_##n;                           \
                                                                                                   \
	DEVICE_DT_INST_DEFINE(n, ti_sn74hc138_init, NULL, &ti_sn74hc138_gpio_data_##n,             \
			      &ti_sn74hc138_gpio_config_##n, POST_KERNEL,                          \
			      CONFIG_GPIO_INIT_PRIORITY, &ti_sn74hc138_gpio_api);

DT_INST_FOREACH_STATUS_OKAY(TI_SN74HC138_GPIO_INIT)
