#!/usr/bin/env python

__author__ = 'Nguyen Duc Trung Dung - ndtdung.blogspot.com'
__email__ = 'ndtdung@spsvietnam.vn/dung.nguyendt@gmail.com'
__version__ = '1.0'
__license__ = 'GPLv2'


import sys
import commands
import optparse
run = commands.getstatusoutput


class PARSER:
    def __init__(self, hostname, community, module, item, range):
        self.hostname = hostname
        self.community = community
        self.module = module
        self.item = item
        self.range = range
        self.module_base_oid = '.1.3.6.1.4.1.13400.2.19.2.'
        self.module_x = 4
        self.cmd = 'snmpget %s -v2c -c %s %s -OqvU'  # get snmp with output options: qvU
        self.list = {'BATTERY VOLTAGE': ['Positive Voltage', 'Negative Voltage'],  # Split items into group
                     'BATTERY CURRENT': ['Positive Current', 'Negative Current'],
                     'BATTERY STATUS': ['Remains Time', 'Temperature', 'Environment Temperature'],
                     'SYSTEM STATUS': ['Status', 'Unit Modules', 'Module Capacity'],
                     'INPUT': ['Input Phase Voltage', 'Input Line Voltage', 'Input Current'],
                     'OUTPUT': ['Output Voltage', 'Output Current', 'Output Active Power', 'Output Load']}
		#Note: It best when one group have only one alarm at time, otherwise the normal range for this one may not suit others. You can split items into more group by edit self.list above.

        self.items = {  # Input
                        # 'name': [.... 'unit', 'alarm or not', 'perf or not']
                        'Input Phase Voltage': ['.1.0', '.2.0', '.3.0', 'V', 'NO', ''],  # no alarm
                        'Input Line Voltage': ['.4.0', '.5.0', '.6.0', 'V', 'NO', ''],
                        'Input Current': ['.7.0', '.8.0', '.9.0', 'A', 'NO', ''],
                        # Output
                        'Output Voltage': ['.16.0', '.17.0', '.18.0', 'V', 'NO', ''],
                        'Output Current': ['.19.0', '.20.0', '.21.0', 'A', 'NO', ''],
                        'Output Active Power': ['.26.0', '.27.0', '.28.0', 'kW', 'NO', ''],
                        'Output Load': ['.35.0', '.36.0', '.37.0', '%', 'YES', 'PERF'],  # alarm, perf
                        # Battery
                        'Positive Voltage': ['.45.0', 'V', 'NO', ''],
                        'Negative Voltage': ['.47.0', 'V', 'NO', ''],
                        'Positive Current': ['.46.0', 'A', 'NO', ''],
                        'Negative Current': ['.48.0', 'A', 'NO', ''],
                        'Remains Time': ['.50.0', 'min', 'NO', 'PERF'],  # perf
                        'Temperature': ['.51.0', 'C', 'YES', 'PERF'],  # alarm, perf
                        'Environment Temperature': ['.52.0', 'C', 'NO', ''],
                        # System
                        'Status': ['.1.3.6.1.4.1.13400.2.19.2.1.1.0', '', 'YES', ''],  # alarm
                        'Unit Modules': ['.1.3.6.1.4.1.13400.2.19.2.3.1.0', '', 'NO', ''],
                        'Module Capacity': ['.1.3.6.1.4.1.13400.2.19.2.3.3.0', 'kV', 'NO', '']}

    def first_blood(self, oid):  # Read SNMP and parse
        if not any(i in self.item for i in self.list.keys()):
            print 'Not supported check TYPE'
            optp.print_help()
            sys.exit(2)
        else:
            _, output = run(self.cmd % (self.hostname, self.community, oid))
            if _ != 0:
                print 'ERROR - %s' % output
                sys.exit(2)
            else:
                raw_data = []
                tmp = output.split('\n')
                for i in range(0, len(tmp)):
                    pre = tmp[i][:-2]  # get integer
                    if not pre:  # adjust zero number
                        pre = '0'
                    sub = tmp[i][-2:]  # get decimal
                    tmp[i] = pre + '.' + sub
                    raw_data.append(float(tmp[i]))  # Save raw data
                return '/'.join(tmp), raw_data

    def raise_alert(self, raw_data, is_alert):
        fst = float(self.range.split(',')[0])
        lst = float(self.range.split(',')[1])
        tmp = []
        if is_alert == 'YES':
            alert = False
            for data in raw_data:
                if fst <= data <= lst:
                    if self.item == 'SYSTEM STATUS':  # translate status
                        data = 'OK'
                    tmp.append(str(data))
                else:
                    alert = True
                    if self.item == 'SYSTEM STATUS':  # translate status
                        data = 'NOT OK (%s)' % data
                    tmp.append(str(data) + '(!!)')
        else:
            alert = False
            for data in raw_data:
                tmp.append(str(data))
        return '/'.join(tmp), alert

    def perf_data(self, name, raw_data, unit, is_alert):
        order = 1
        perf = []
        for data in raw_data:
            if len(raw_data) > 1:
                name_tmp = name + str(order)
            else:
                name_tmp = name
            if self.range and is_alert == 'YES':
                fst = int(self.range.split(',')[0])
                lst = int(self.range.split(',')[1])
            else:
                fst = ''
                lst = ''
            perf.append('%s=%d%s;%s;%s;;' % (name_tmp, data, unit, fst, lst))
            order += 1
        return ' '.join(perf)

    def count_enemy(self):
        oid = self.items['Unit Modules'][0]
        blood, tmp = self.first_blood(oid)
        if self.module > float(blood):
            print 'ERROR - You requested module %d but there is only %s module installed.' % (self.module, blood.split('.')[0])
            sys.exit(2)
        else:
            _ = self.module_base_oid + str(self.module_x + int(blood.split('.')[0]))
            return _  # number of module installed

    def sniper(self, base_oid):
        oids = []
        out_screen = []
        try:
            bodies = self.list[self.item]
        except KeyError as error:
            print 'ERROR - Invalid type'
            optp.print_help()
            sys.exit(1)
        exitcode = None
        perf = ['']
        for body in bodies:
            for tmp in range(0, len(self.items[body][:-3])):
                self.items[body][tmp] = base_oid + self.items[body][tmp]
            oids.append([body, ' '.join(self.items[body][:-3]), self.items[body][-3], self.items[body][-2], self.items[body][-1]])
        for o in range(0, len(oids)):
            name = oids[o][0]
            oid = oids[o][1]
            value, raw_data = self.first_blood(oid)
            unit = oids[o][2]
            is_alert = oids[o][-2]  # alarm option?
            if oids[o][-1] == 'PERF':  # enable perf data
                perf.append(self.perf_data(name, raw_data, unit, is_alert))
            if self.item == 'SYSTEM STATUS':
                self.range = '0,0'
            if self.range is None:
                alert = False
                out_screen.append(('%s: %s %s' % (name, value, unit)).strip())
            else:
                value_2, alert = self.raise_alert(raw_data, is_alert)
                out_screen.append(('%s: %s %s' % (name, value_2, unit)).strip())
            if alert:
                exitcode = 2
            if not alert and exitcode != 2:
                exitcode = 0
        return out_screen, exitcode, perf

    def main(self):
        if self.item == 'SYSTEM STATUS':  # do not use base_oid for SYSTEM STATUS
            base_oid = ''
        else:
            base_oid = self.count_enemy()
        out_screen, exitcode, perf = self.sniper(base_oid)
        ecd = {0: 'OK', 2: 'CRIT'}
        if len(perf) > 1:
            perf[0] = '|'
        print '%s - %s %s' % (ecd[exitcode], ', '.join(out_screen), ' '.join(perf))
        sys.exit(exitcode)

if __name__ == '__main__':
    optp = optparse.OptionParser()
    optp.add_option('-H', '--host', help='hostname or IP address', dest='host')
    optp.add_option('-c', help='SNMP community', dest='community')
    optp.add_option('-t', '--type', help='BATTERY VOLTAGE, BATTERY CURRENT, BATTERY STATUS, SYSTEM STATUS, INPUT, OUTPUT', dest='type')
    optp.add_option('-m', '--module', help='module to check', dest='module', type='int')
    optp.add_option('-a', '--range', help='normal range, when something out of scope alert will be raised. Ex: -a 0,80', dest='range', type='string')
    opts, args = optp.parse_args()

    if opts.community is None or opts.host is None:
        optp.print_help()
        sys.exit(1)

    if opts.module is None and opts.type != 'SYSTEM STATUS':
        print 'You must specify module number'
        sys.exit(1)
    else:
        if opts.type is None:
            print 'What info do you need to check?'
            sys.exit(1)

    #GET UPS SYSTEM INFO
    PARSER(opts.host, opts.community, opts.module, opts.type, opts.range).main()
