from art import art


def coffee(amount: int = 1) -> str:
    """
    Generate some coffee.

    Parameters:
        amount (int): The number of coffee cups to generate. Defaults to 1.

    Returns:
        str: The ASCII art representation of the coffee cups.
    """
    ascii_art = art("coffee", number=amount)
    return ascii_art
