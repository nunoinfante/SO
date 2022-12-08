with open('file10.txt', 'r') as input:
    texto = input.readlines()
    new_list = [item.strip() for item in texto]
    with open('file11.txt', 'w') as output:
        for i, s in enumerate(new_list):
            output.write(f'{s}{i}\n')