"""Decode desktop and common xterm numeric-keypad input sequences."""

KEYPAD_SEQUENCES = {
    '\x1bOq': '1',
    '\x1bOt': '4',
    '\x1b[1~': '1',
    '\x1b[4~': '4',
    '\x1b[F': '1',
    '\x1b[D': '4',
}


def extract_patrol_keys(buffer: str) -> tuple[list[str], str]:
    """Return recognized 1/4 keys and any incomplete terminal sequence."""
    keys = []
    sequences = sorted(KEYPAD_SEQUENCES, key=len, reverse=True)
    while buffer:
        matched = next(
            (sequence for sequence in sequences if buffer.startswith(sequence)),
            None,
        )
        if matched is not None:
            keys.append(KEYPAD_SEQUENCES[matched])
            buffer = buffer[len(matched):]
            continue
        if any(sequence.startswith(buffer) for sequence in sequences):
            break
        character = buffer[0]
        buffer = buffer[1:]
        if character in ('1', '4'):
            keys.append(character)
    return keys, buffer
