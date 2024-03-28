def remove_keys_recursive(d, keys):
    for k in keys:
        if k in d:
            del d[k]
    for k, v in d.items():
        if isinstance(v, dict):
            remove_keys_recursive(v, keys)
        elif isinstance(v, list):
            for i in v:
                if isinstance(i, dict):
                    remove_keys_recursive(i, keys)


# NOTE this uses quite a primitive check for cuids but I do not think it is worth coming up with a better one
# Also this function is NOT written with performance in mind, good for small to mid size dicts like we have in our test
def rename_cuid_key_recursive(d):
    new_key = '<cuid>'
    for k in list(d.keys()):
        if len(k) == 25 and not k.isalpha():  #primitive check for cuid
            d[new_key] = d.pop(k)
    for k, v in d.items():
        if isinstance(v, dict):
            rename_cuid_key_recursive(v)
        elif isinstance(v, list):
            for i in v:
                if isinstance(i, dict):
                    rename_cuid_key_recursive(i)


INTEGRATION_SNAPSHOT_DIRECTORY = 'tests/integration/snapshots'
