from yapf.yapflib.yapf_api import FormatCode
import json
import glob


def format_cell(source):
    for line in source.split('\n'):
        if line.strip().startswith(('!', '%')):
            return source
    return FormatCode(source, style_config="google")[0]


def format_file(file_name):
    with open(file_name, 'r') as file:
        data = json.load(file)

    idx = 1
    for cell in data['cells']:
        if cell['cell_type'] == 'code':
            cell['execution_count'] = idx
            if isinstance(cell['source'], list):
                cell['source'] = ''.join(cell['source'])
            cell['source'] = format_cell(cell['source'])
            idx += 1
            if cell['source'].endswith('\n'):
                cell['source'] = cell['source'][:-1]

    with open(file_name, 'w') as file:
        file.write(json.dumps(data, indent=4))
    print("Formatted", file_name)


if __name__ == '__main__':
    for file in glob.glob("*/*.ipynb"):
        format_file(file)
