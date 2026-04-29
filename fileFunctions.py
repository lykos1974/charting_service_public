import os
import json
import logging as Logger

# This variable holds the path separator of the specific operating system on which the application runs
PATH_SEPARATOR = os.path.sep

Logger.basicConfig(level=Logger.INFO)

def is_dir_exist(dirpath = ''):
    if dirpath == '':
        Logger.error('[is_dir_exist]: invalid argument in function. Exiting...')
        exit(1)
    else:
        if os.path.exists(dirpath):
            return True
        else:
            return False

def is_file_exist(filepath=''):
    if filepath == '':
        Logger.error('[is_file_exist]: invalid argument in function. Exiting...')
        exit(1)
    else:
        if os.path.isfile(filepath):
            return True
        else:
            return False

def create_dir(dirpath = ''):
    if dirpath == '':
        Logger.error('[create_dir]: invalid argument in function. Exiting...')
        exit(1)
    else:
        if not is_dir_exist(dirpath):
            Logger.info('[create_dir]: Creating directory path ' + dirpath + '.')
            try:
                os.makedirs(dirpath)
            except:
                Logger.error('[create_dir]: Fail to create directories path. Exiting...')
                exit(1)
        else:
            Logger.info('[create_dir]: Directory path ' + dirpath + ' already exist. Nothing to create.')

def file_get_contents(filepath):
    if is_file_exist(filepath):
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except:
             Logger.error('[file_get_contents] Fail to open file for read. Exiting...')
             exit(1)
    else:
        Logger.error('[file_get_contents] File you try to open does not exist. Exiting...')
        exit(1)

def file_get_json_contents(filepath):
    return json.loads(file_get_contents(filepath))

def file_save_contents(filepath, data):
    if is_file_exist(filepath):
        try:
            with open(filepath, 'a') as f:
                f.write(data)
        except:
             Logger.error('[file_save_contents] Fail to open file for append. Exiting...')
             exit(1)
    else:
        try:
            with open(filepath, 'w') as f:
                f.write(data)
        except:
             Logger.error('[file_save_contents] Fail to open file for writing. Exiting...')
             exit(1)

def file_save_json_contents(filepath, data):
    if is_file_exist(filepath):
        json_data = file_get_json_contents(filepath)
        if data:
            if type(data) == type([]):
                for i in data:
                    if type(i) == type({}):
                        json_data.append(i)
                    else:
                        json_data.append(json.dumps(i))
            elif type(data) == type({}):
                json_data.append(data)
            else:
                json_data.append(json.dumps(data))
            try:
                with open(filepath, 'w') as outfile:
                    json.dump(json_data, outfile)
            except:
                Logger.error('[file_save_json_contents] Fail to open file for writing. Exiting...')
                exit(1)
    else:
        try:
            json_data = []
            if type(data) != type([]):
                if type(data) == type({}):
                    json_data.append(data)
                else:
                    json_data.append(json.dumps(data))
            else:
                json_data = data

            with open(filepath, 'w') as outfile:
                json.dump(json_data, outfile)
        except:
            Logger.error('[file_save_json_contents] Fail to open file for writing. Exiting...')
            exit(1)

def file_delete(filepath):
    if is_file_exist(filepath):
        try:
            os.remove(filepath)
        except:
            Logger.error('[file_delete] Fail to remove file. Exiting...')
            exit(1)
    else:
        Logger.info('[file_delete] The file you tried to delete ' + filepath + ', does not exist. Exiting.')
        return


if __name__ == "__main__":
    exit(1)