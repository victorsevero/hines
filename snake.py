import struct

import numpy as np
import pygame

from cpu import CPU

SCALE_FACTOR = 30
SCREEN_SIZE = 32
BG_COLOR = (0, 0, 0)
SNAKE_COLOR = (0, 255, 0)
FOOD_COLOR = (255, 255, 255)

KEY_MAPPINGS = {
    pygame.K_UP: 0x77,
    pygame.K_DOWN: 0x73,
    pygame.K_LEFT: 0x61,
    pygame.K_RIGHT: 0x64,
}

SCREEN_ADDRESS = 0x200

pygame.init()
display = pygame.display.set_mode(
    (SCALE_FACTOR * SCREEN_SIZE, SCALE_FACTOR * SCREEN_SIZE)
)
pygame.display.set_caption("6502 Snake Game")
prev_screen = None


class FPS:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(pygame.font.match_font("ubuntumono"), 40)
        self.text = self.font.render(
            str(self.clock.get_fps()),
            True,
            FOOD_COLOR,
        )

    def render(self, display: pygame.display):
        self.text = self.font.render(
            str(round(self.clock.get_fps())).rjust(3),
            True,
            FOOD_COLOR,
        )
        display.blit(self.text, (10, 10))


fps = FPS()


def read_snake_data():
    with open("snake.bin", "rb") as fp:
        bin_data = fp.read()
    data_len = len(bin_data) // struct.calcsize("B")
    data = struct.unpack("<" + "B" * data_len, bin_data)
    return np.array(data, dtype=np.uint8)


def callback(cpu: CPU):
    global prev_screen
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                cpu.bus.write(0xFF, 0x77)
            elif event.key == pygame.K_DOWN:
                cpu.bus.write(0xFF, 0x73)
            elif event.key == pygame.K_LEFT:
                cpu.bus.write(0xFF, 0x61)
            elif event.key == pygame.K_RIGHT:
                cpu.bus.write(0xFF, 0x64)

    screen = cpu.bus.read_chunk(SCREEN_ADDRESS, SCREEN_SIZE**2)
    if np.array_equal(screen, prev_screen):
        prev_screen = screen
        return

    display.fill(BG_COLOR)
    # it would be more efficient if we checked for snake body parts and food
    # positions from memory, but meh
    update = False
    for address in range(SCREEN_ADDRESS, SCREEN_ADDRESS + SCREEN_SIZE**2):
        x = (address - SCREEN_ADDRESS) % SCREEN_SIZE
        y = (address - SCREEN_ADDRESS) // SCREEN_SIZE
        pixel_ram_value = cpu.bus.read(address)
        match pixel_ram_value:
            case 0x00:
                color = BG_COLOR
            case 0x01:
                color = SNAKE_COLOR
            case _:
                color = FOOD_COLOR
        if (
            display.get_at(
                (
                    SCALE_FACTOR * x + SCALE_FACTOR // 2,
                    SCALE_FACTOR * y + SCALE_FACTOR // 2,
                )
            )[:3]
            != color
        ):
            update = True
            pygame.draw.rect(
                display,
                color,
                [
                    SCALE_FACTOR * x,
                    SCALE_FACTOR * y,
                    SCALE_FACTOR,
                    SCALE_FACTOR,
                ],
            )

    prev_screen = screen
    fps.render(display)
    if update:
        pygame.display.update()
    fps.clock.tick()


def screen_dump(cpu: CPU):
    data = cpu.bus.data[SCREEN_ADDRESS : SCREEN_ADDRESS + SCREEN_SIZE**2]
    data = data.reshape(32, 32)
    np.savetxt("screen.csv", data, fmt="%d", delimiter=",")


def run():
    cpu = CPU()
    cpu.load_rom("snake.nes")
    # cpu.bus.write16(0xFFFC, 0x0600)
    cpu.reset()

    game_over = False
    rng = np.random.default_rng()
    while not game_over:
        cpu.bus.write(0xFE, rng.integers(low=0, high=255, dtype=np.uint8))
        callback(cpu)
        opcode = cpu.bus.read(cpu.program_counter.read())
        cpu.operation(opcode)
        if cpu.program_counter.read() == 0x735:
            game_over = True


if __name__ == "__main__":
    run()
