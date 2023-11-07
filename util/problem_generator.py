import random


def generate_arithmetic_problems(num_problems, seed=None):
    if seed is not None:
        random.seed(seed)

    for _ in range(num_problems):
        operation = random.choice(
            ['addition', 'subtraction', 'multiplication', 'division'])

        if operation == 'addition':
            num1 = random.randint(2, 100)
            num2 = random.randint(2, 100)
            problem = f"{num1} + {num2}"
            answer = str(num1 + num2)
        elif operation == 'subtraction':
            num1 = random.randint(2, 100)
            num2 = random.randint(2, num1)
            problem = f"{num1} - {num2}"
            answer = str(num1 - num2)
        elif operation == 'multiplication':
            num1 = random.randint(2, 12)
            num2 = random.randint(2, 100)
            problem = f"{num1} × {num2}"
            answer = str(num1 * num2)
        elif operation == 'division':
            num2 = random.randint(2, 12)
            result = random.randint(2, 100)
            num1 = result * num2
            problem = f"{num1} ÷ {num2}"
            answer = str(result)

        yield {"problem": problem, "answer": answer}
