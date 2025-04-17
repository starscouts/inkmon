#
#  Equestria.Dev InkMon System Software
#
#  This is the system software for the InkMon project. To run this, you will need
#  to flash this Python file as main.py on a Badger 2040W. Make sure you also have
#  the WIFI_CONFIG.py file to be able to connect to a Wi-Fi network.
#
#  Note: this code is not intended to run on regular Python or on non-Badger 2040W
#  hardware.
#

import badger2040
# noinspection PyUnresolvedReferences
import network
import socket
import sys
import os
import platform
# noinspection PyUnresolvedReferences
import machine
import gc

VERSION = "1.1"

print("Equestria.dev InkMon v" + VERSION)

print("Connecting to network...")

display = badger2040.Badger2040()
display.led(255)
# noinspection PyUnresolvedReferences
display.connect()
net = network.WLAN(network.STA_IF).ifconfig()


def get_system_info():
    gc.collect()

    # noinspection PyUnresolvedReferences
    return "Syst:Soft:Vers:" + VERSION + "\r\n" + \
        "Syst:Soft:PyVs:" + sys.version + "\r\n" + \
        "Syst:Soft:Mods:" + ",".join(sys.modules.keys()) + "\r\n" + \
        "Syst:Soft:Libc:" + ",".join(platform.libc_ver()) + "\r\n" + \
        "Syst:Hard:Mach:" + os.uname().machine + "\r\n" + \
        "Syst:Hard:Freq:" + str(machine.freq()) + "\r\n" + \
        "Syst:Hard:MemT:" + str(gc.mem_free() + gc.mem_alloc()) + "\r\n" + \
        "Syst:Hard:MemF:" + str(gc.mem_free())


if net:
    print("Connected to network as " + net[0] + "/" + net[1] + " through " + net[2])
    print("DNS server is " + net[3])

    # noinspection PyUnresolvedReferences
    display.set_pen(0)
    display.clear()
    display.update()

    display.led(0)

    addr = socket.getaddrinfo('0.0.0.0', 24910)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)

    while True:
        cl, addr = s.accept()
        display.led(1)

        try:
            cl_file = cl.makefile('rwb', 0)
            # noinspection PyTypeChecker
            cl.send("# If you're reading this, why do you hate yourself so much?\r\n")
            # noinspection PyTypeChecker
            cl.send("Proc:Glob:GBeg\r\n")
            data = ""

            while True:
                line = cl_file.readline()
                data += line.decode("utf-8")
                if not line or line == b'\r\n':
                    break

            # noinspection PyTypeChecker
            cl.send(get_system_info() + "\r\n")

            try:
                # noinspection PyTypeChecker
                cl.send("# Getting data ready for compilation\r\n")
                # noinspection PyTypeChecker
                cl.send("Proc:CPyt:Size:" + str(len(data)) + "\r\n")
                # noinspection PyTypeChecker
                cl.send("Proc:CPyt:PyCC\r\n")
                # noinspection PyTypeChecker
                cl.send("# Compiling code\r\n")
                c = compile(data, "input.py", "exec")
                # noinspection PyTypeChecker
                cl.send("Proc:CPyt:Stat:00\r\n")
                # noinspection PyTypeChecker
                cl.send("# Compiler OK\r\n")
                # noinspection PyTypeChecker
                cl.send("Proc:Runt:LdRT\r\n")

                try:
                    # noinspection PyTypeChecker
                    cl.send("# Running program\r\n")
                    exec(data)
                    # noinspection PyTypeChecker
                    cl.send("# Runtime OK\r\n")
                    # noinspection PyTypeChecker
                    cl.send("Proc:Runt:Stat:00\r\n")
                    # noinspection PyTypeChecker
                    cl.send("Proc:Glob:Stat:10\r\n")
                except Exception as e:
                    # noinspection PyTypeChecker
                    cl.send("# Error while running\r\n")
                    # noinspection PyTypeChecker
                    cl.send("Proc:Runt:Stat:10\r\n")
                    # noinspection PyTypeChecker
                    cl.send("Proc:Glob:Stat:40\r\n")
                    # noinspection PyTypeChecker
                    cl.send("Proc:Glob:ErrM:" + str(e) + "\r\n")
            except Exception as e:
                # noinspection PyTypeChecker
                cl.send("# Error while compiling\r\n")
                # noinspection PyTypeChecker
                cl.send("Proc:CPyt:Stat:10\r\n")
                # noinspection PyTypeChecker
                cl.send("Proc:Glob:Stat:30\r\n")
                # noinspection PyTypeChecker
                cl.send("Proc:Glob:ErrM:" + str(e) + "\r\n")

            # noinspection PyTypeChecker
            cl.send("Proc:Glob:GEnd\r\n")
            # noinspection PyTypeChecker
            cl.send("# (c) Equestria.dev Developers\r\n")
            cl.close()
            display.led(0)
        except Exception as e:
            print(e)

            try:
                # noinspection PyTypeChecker
                cl.send("# General system failure, is hardware faulty?\r\n")
                # noinspection PyTypeChecker
                cl.send("Proc:Glob:Fail\r\n")
                # noinspection PyTypeChecker
                cl.send("Proc:Glob:Stat:20\r\n")
                # noinspection PyTypeChecker
                cl.send("Proc:Glob:ErrM:" + str(e) + "\r\n")

                cl.close()
                display.led(0)
            except Exception as e:
                print(e)

else:
    raise Exception("Failed to connect to network.")
