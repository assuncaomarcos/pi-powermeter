#!/usr/bin/env python3
"""
================================================
Script that measures the voltage of an ADC and a differential ADC
and computes the amount of power drawn by 5V lines
================================================
Author: Marcos Dias de Assuncao
"""

from __future__ import absolute_import, unicode_literals
from argparse import ArgumentParser
from configparser import ConfigParser, Error
import time
import signal
import sys


class HexConfigParser(ConfigParser):

    def __init__(self, **kwargs):
        super(ConfigParser, self).__init__(**kwargs)

    def gethex(self, section, option):
        return int(self.get(section, option), 16)


try:
    from ADCPi import ADCPi
    from ADCDifferentialPi import ADCDifferentialPi
except ImportError:
    print("Failed to import ADCPi library from python system path")
    print("Importing from parent folder instead")
    try:
        sys.path.append('..')
        from ADCPi import ADCPi
        from ADCDifferentialPi import ADCDifferentialPi
    except ImportError:
        raise ImportError(
            "Failed to import teh ADC library from parent folder")


def parse_options():
    """Parse the command line options for the measurement application"""
    parser = ArgumentParser(description='Measures the power drawn by USB ports.')

    parser.add_argument('--config', dest='config', type=str, required=True,
                        help='the path to the configuration file')

    parser.add_argument('--output', dest='output', type=str, required=True,
                        help='the path to the output file')

    args = parser.parse_args()
    return args


def measure(config, out_file):
    """
    Main program function
    """
    # Measurement frequency in milliseconds
    interval = config.getfloat("DEFAULT", "frequency") / 1000

    section = "ADC"
    address1 = config.gethex(section, "address1")
    address2 = config.gethex(section, "address2")
    bit_rate = config.getint(section, "bit_rate")
    ref_channel = config.getint(section, "ref_channel")
    conversion_mode = config.getint(section, "conversion_mode")
    pga = config.getint(section, "pga")

    # ADC measuring the value of the input voltage
    adc_in = ADCPi(address1, address2, bit_rate)
    adc_in.set_conversion_mode(conversion_mode)
    adc_in.set_pga(pga)

    section = "ADC_DIFF"
    address1 = config.gethex(section, "address1")
    address2 = config.gethex(section, "address2")
    bit_rate = config.getint(section, "bit_rate")
    conversion_mode = config.getint(section, "conversion_mode")
    pga = config.getint(section, "pga")

    # Differential ADC measuring the voltage drop across shunt resistors
    adc_diff = ADCDifferentialPi(address1, address2, bit_rate)
    adc_diff.set_conversion_mode(conversion_mode)
    adc_diff.set_pga(pga)

    section = "DEVICES"
    devices = config.get(section, "ids").split(",")
    resistors = [float(x) for x in config.get(section, "resistors").split(",")]
    channels = [int(x) for x in config.get(section, "channels").split(",")]

    out = open(out_file, 'w')
    out.write("timestamp " + (len(devices) * "%s " % tuple(devices)) + "\n")
    try:
        while True:
            in_volt = adc_in.read_voltage(ref_channel)
            power = []

            # First measure and then compute the power
            for i in range(len(devices)):
                power.append((adc_diff.read_voltage(channels[i]) * in_volt) / resistors[i])

            out.write(((len(devices) + 1) * "%f " + "\n") % ((time.time(),) + tuple(power)))
            time.sleep(interval)
    finally:
        out.close()


def signal_handler(signal, frame):
    print('Stopping...')
    sys.exit(0)


def main():
    opts = parse_options()
    try:
        config = HexConfigParser()
        config.read(opts.config)
    except Error:
        raise ImportError("Failed to read the configuration file")

    signal.signal(signal.SIGINT, signal_handler)
    print("Measuring... (Press Ctrl+C to stop)")
    measure(config, opts.output)


if __name__ == "__main__":
    main()
