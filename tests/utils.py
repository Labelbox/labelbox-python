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
