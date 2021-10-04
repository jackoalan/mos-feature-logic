import csv
import os
import re
import sys
from distutils.util import strtobool


class Machine:
    def __init__(self):
        self.opcode_set = set()
        self.feature_dict = {}

    def __repr__(self):
        return f'Machine(opcodes={self.opcode_set}, features={self.feature_dict})'

    def parse_opcodes(self, path):
        with open(path, newline='') as f:
            reader = csv.reader(f, skipinitialspace=True)
            opcode = 0
            for row in reader:
                for col in row:
                    if col:
                        self.opcode_set.add((opcode, col))
                    opcode += 1

    def parse_features(self, path):
        with open(path, newline='') as f:
            reader = csv.DictReader(f, skipinitialspace=True)
            for row in reader:
                for k, v in row.items():
                    try:
                        self.feature_dict[k] = bool(strtobool(v))
                    except ValueError:
                        pass
                break


class CombinationFinder:
    MACHINE_FILE_RE = re.compile(r'(\w+)_(features|opcodes)\.csv')

    def __init__(self):
        self.machines = {}
        self.all_features = set()

    def __repr__(self):
        return repr(self.machines)

    def load_machines(self, path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                name_match = CombinationFinder.MACHINE_FILE_RE.match(name)
                if name_match is not None:
                    machine_name = name_match.group(1)
                    machine = self.machines.setdefault(machine_name, Machine())
                    file_type = name_match.group(2)
                    if file_type == 'opcodes':
                        machine.parse_opcodes(os.path.join(root, name))
                    elif file_type == 'features':
                        machine.parse_features(os.path.join(root, name))

    def expand_features(self):
        # Convert all opcodes into individual features and build global feature set
        all_opcode_tuples = set()
        for machine in self.machines.values():
            for opcode_tuple in machine.opcode_set:
                opcode, _ = opcode_tuple
                all_opcode_tuples.add(opcode_tuple)
                self.all_features.add(opcode_tuple)
            for feature_name, _ in machine.feature_dict.items():
                self.all_features.add(feature_name)

        # Merge opcode features back into machines including opcodes for other machines as False
        for machine in self.machines.values():
            for opcode_tuple in all_opcode_tuples:
                machine.feature_dict[opcode_tuple] = False
            for opcode_tuple in machine.opcode_set:
                if opcode_tuple in all_opcode_tuples:
                    machine.feature_dict[opcode_tuple] = True

    def find_combinations(self):
        # Transpose the data into feature combinations by machine
        features_by_machines = {}
        machine_list = sorted(self.machines.keys())
        for feature in self.all_features:
            machines = []
            for machine_name in machine_list:
                machine = self.machines[machine_name]
                if feature in machine.feature_dict:
                    state = machine.feature_dict[feature]
                    machines.append(machine_name if state else ('~' + machine_name))
            opcodes, machine_features = features_by_machines.setdefault(tuple(machines), ([], []))
            if type(feature) is tuple:
                opcodes.append(feature)
            else:
                machine_features.append(feature)

        # Return as sorted list for determinism
        machine_set_list = sorted(features_by_machines.keys())
        sorted_result = []
        for machine_set in machine_set_list:
            opcodes, machine_features = features_by_machines[machine_set]
            sorted_result.append((machine_set, (sorted(opcodes), sorted(machine_features))))

        return sorted_result

    def run(self, path):
        self.load_machines(path)
        self.expand_features()
        return self.find_combinations()


if __name__ == '__main__':
    script_relative_machines = os.path.join(os.path.dirname(__file__), 'machines')
    if len(sys.argv) > 1:
        if not os.path.isdir(sys.argv[1]):
            raise RuntimeError(f'{sys.argv[1]} is not a directory')
        path = sys.argv[1]
    elif os.path.isdir('machines'):
        path = 'machines'
    elif os.path.isdir(script_relative_machines):
        path = script_relative_machines
    else:
        raise RuntimeError('unable to locate machines directory')

    from machine_set_aliases import MACHINE_SET_ALIASES

    finder = CombinationFinder()
    arrs = []
    all_features = []
    combinations = finder.run(path)
    for machine_set, features in combinations:
        opcodes, machine_features = features
        for machine_feature in machine_features:
            if machine_feature not in all_features:
                all_features.append(machine_feature)
    for machine_set, features in combinations:
        opcodes, machine_features = features
        machine_set_name = MACHINE_SET_ALIASES.get(machine_set, machine_set)

        arr_out = [''] * 256

        print(f'{machine_set_name} opcodes=[')
        for opcode, mnemonic in opcodes:
            print(f'  ({hex(opcode)}, \'{mnemonic}\'),')
            arr_out[opcode] = mnemonic
        print(']')

        print(f'{machine_set_name} features=[')
        for machine_feature in machine_features:
            print(f'  \'{machine_feature}\',')
        print(']')

        for machine_feature in all_features:
            if machine_feature in machine_features:
                arr_out.append('X')
            else:
                arr_out.append('')

        arr_out2 = [str(machine_set)]
        arr_out2.extend(arr_out)
        arrs.append(arr_out2)

    for i in range(257 + len(all_features)):
        items = ['' if i == 0 else hex(i - 1)]
        if i == 0:
            items = ['']
        elif 1 <= i <= 256:
            items = [hex(i - 1)]
        else:
            items = [all_features[i - 257]]

        for arr in arrs:
            items.append(arr[i])
        print('\t'.join(items))
