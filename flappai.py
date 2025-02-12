import pygame
import random
import neat
import os
pygame.font.init()

# Constants for game screen
WIN_WIDTH = 575
WIN_HEIGHT = 800

GEN = 0

# Load images
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png"))),
    ]
PIPE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont(("timesnewroman"), 50)


class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROTATION_VELOCITY = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        """
        Initialize a Bird object with specified x and y coordinates.
        :param x: The initial x-coordinate for the bird's position.
        :param y: The initial y-coordinate for the bird's position.
        :return: None
        """
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.velocity = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        Make the bird jump by setting the velocity to a negative number and resetting
        the tick count and height.
        :return: None
        """
        self.velocity = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """
        Move the bird by calculating its displacement based on its velocity and
        the number of frames since the last jump. The bird's y-coordinate is updated
        accordingly.
        The bird's tilt is also updated to give the illusion of up and down movement.
        If the bird is moving upwards, its tilt is increased to give the illusion of
        climbing. If the bird is moving downwards, its tilt is decreased to give the
        illusion of falling.
        :return: None
        """
        self.tick_count += 1

        # Calculating movement of pixels per frame to give the impression of an arc
        displacement = self.velocity*(self.tick_count) + 1.5*(self.tick_count)**2

        if displacement >= 16:
            displacement = (displacement/abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        # Tilt the bird upwards when jumping
        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else: # Tilt the bird downwards
            if self.tilt > -90:
                self.tilt -= self.ROTATION_VELOCITY

    def draw(self, win):
        """
        Draw the bird on the screen
        :param win: pygame window
        :return: None
        """
        self.img_count += 1

        # What image should we show based on the img_count
        # If img_count is less than ANIMATION_TIME, show the first image
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        # If img_count is less than ANIMATION_TIME*2, show the second image, etc.
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # If the bird is falling, don't flap the wings
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # Rotate the bird image around the center
        rotated_image = pygame.transform.rotate(self.img, self.tilt)

        # This part is from stack overflow
        new_rectangle = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rectangle.topleft)

    def get_mask(self):
        """
        Get the mask for the current image of the bird.
        :return: A pygame mask object for the current image of the bird.
        """
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200 # Space between the pipes
    VELOCITY = 5 # Speed at which the pipes "move"

    def __init__(self, x):
        """
        Init a Pipe object with a given x-coordinate.
        :param x: The x-coordinate for the pipe's position.
        :return: None
        """
        self.x = x
        self.height = 0
        self.gap = 100
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE, False, True)
        self.PIPE_BOTTOM = PIPE
        self.passed = False
        self.set_height()

    def set_height(self):
        """
        Set the height of the pipe by generating a random y-coordinate between 50 and 450.
        :return: None
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        Move the pipe to the left by the VELOCITY amount to create the illusion of movement.
        :return: None
        """
        self.x -= self.VELOCITY

    def draw(self, win):
        """
        Draw the top and bottom pipes onto the window at the specified x and y coordinates.
        :param win: Pygame window
        :return: None
        """
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        """
        Check if the bird has collided with the pipe.
        :param bird: A Bird object.
        :return: True if a collision has occurred, False otherwise.
        """
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y)) # Can't be decimal so round it
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)
        top_point = bird_mask.overlap(top_mask, top_offset)

        if top_point or bottom_point:
            return True
        return False


class Base:
    VELOCITY = 5 # Needs to be same as Pipe, or else it looks like they are moving at different speeds
    WIDTH = BASE.get_width()
    IMG = BASE

    def __init__(self, y):
        """
        Init the Base object with a specific y-coordinate.
        :param y: The y-coordinate for the base's position on the screen.
        :return: None
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        Move the base to the left by the VELOCITY amount to create the illusion of movement.
        If the first image is off the screen to the left, reset it to the right of the second image.
        If the second image is off the screen to the left, reset it to the right of the first image.
        :return: None
        """
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Draw the two base images onto the window at the specified x and y coordinates.
        This creates the illusion of the base moving left by drawing the same image twice
        at different x-coordinates and then offsetting them by the width of the image.
        :param win: Pygame window
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def create_window(win, birds, pipes, base, score, gen):
    """
    Draw all the game objects onto the window, then update the display.
    This function is called once per frame in the main game loop.
    :param win: Pygame window
    :param birds: List of Bird objects to draw
    :param pipes: List of Pipe objects to draw
    :param base: Base object to draw
    :param score: The score to display in the top right of the window
    :param gen: The current generation to display in the top left of the window
    :return: None
    """
    win.blit(BG, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("SCORE: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    text = STAT_FONT.render("GEN: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))

    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()

def main(genomes, config):
    """
    Main function to run the game. This function initializes the game window, sets up the game objects, and enters
    the main game loop. The main game loop checks for collisions between the bird and the pipes, updates the
    positions of the pipes and the base, and redraws the window with the updated positions.
    :param genomes: List of tuples containing the genome id and the genome object
    :param config: Config file for NEAT algorithm
    :return: None
    """
    global GEN
    GEN += 1
    nets = []
    geno = []
    birds = []

    for _, g in genomes: # genomes is a tuple that has the genome id and the genome object
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        geno.append(g)


    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_index = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_index = 1
        else:
            run = False
            break


        for bird in list(birds):
            bird.move()
            geno[birds.index(bird)].fitness += 0.1

            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_index].height), abs(bird.y - pipes[pipe_index].bottom)))

            if output[0] > 0.5:
                bird.jump()


        add_pipe = False
        removed_pipes = []
        for pipe in pipes:
            for bird in list(birds):
                if pipe.collide(bird):
                    geno[birds.index(bird)].fitness -= 1 # less favoured if it hits a pipe
                    nets.pop(birds.index(bird))
                    geno.pop(birds.index(bird))
                    birds.remove(bird)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0: # if pipe is off the screen
                removed_pipes.append(pipe)


            pipe.move()

        if add_pipe:
            score += 1
            for g in geno:
                g.fitness += 5 # more favoured if it passes a pipe
            pipes.append(Pipe(600))

        for removed in removed_pipes:
            pipes.remove(removed)

        for bird in list(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                nets.pop(birds.index(bird))
                geno.pop(birds.index(bird))
                birds.remove(bird)

        if score > 60:
            break

        base.move()
        create_window(win, birds, pipes, base, score, GEN)


def run(config_path):
    """
    Run the NEAT algorithm to evolve a solution for the Flappy Bird game.
    This function initializes the NEAT configuration from the given config file,
    creates a population, and adds reporters to observe the evolutionary process.
    It then runs the main function for a specified number of generations to evolve
    the neural networks controlling the birds.
    :param config_path: Path to the NEAT configuration file.
    :return: None
    """

    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                        neat.DefaultStagnation, config_path)

    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    winner = population.run(main, 50) # 50 is the number of generations to pass to main()


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "neat-config.txt")
    run(config_path)



