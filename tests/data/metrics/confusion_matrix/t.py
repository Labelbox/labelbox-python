import json

chain = dict()
t = 3
for a0 in range(t):
    nn = 4
    answer = dict()
    for n in range(1, nn + 1):
        vals = []
        offset = 0
        vals.append(n)  #[2, 1]
        while (not n == 1):
            if (n % 2):
                n = 3 * n + 1
            else:
                n //= 2
            vals.append(n)
        for index, val in enumerate(vals):
            chain[val] = len(vals) - index + offset - 1

        print(n)
        answer[n] = chain[n]
    print(json.dumps(answer, sort_keys=True))
