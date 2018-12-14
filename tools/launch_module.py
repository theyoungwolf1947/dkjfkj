import os
import argparse
import libs.reader as reader

#launch specified module no all plan in blueprint

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--module", help="choose launched module",
                        default="grid")
    args = parser.parse_args()
    module = args.module
    num_files = len(reader.DEFAULT_BLUEPRINT_INPUT_FOLDER)
    for index_plan in range(num_files):
        print("index_plan", type(index_plan))
        command_lauch_grid = "python ../libs/" + module + ".py -p " + str(index_plan)
        os.system(command_lauch_grid)
