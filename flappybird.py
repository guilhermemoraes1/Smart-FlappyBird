import pygame
import os
import random
import neat

ia_playing = True
generation = 0

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 700

PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
FLOOR_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BACKGROUND_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))
BIRDS_IMAGES = [
  pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
  pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
  pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))
]

pygame.font.init()
POINTS_FONT = pygame.font.SysFont('arial', 30)

class Passaro():
  IMGS = BIRDS_IMAGES
  # animações da rotação
  MAXIMUM_ROTATION = 25
  ROTATION_SPEED = 20
  ANIMATION_TIME = 5

  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.angle = 0
    self.speed = 0
    self.height = self.y
    self.time = 0
    self.contagem_imagem = 0
    self.imagem = self.IMGS[0]

  def jump(self):
    self.speed = -10.5
    self.time = 0
    self.height = self.y

  def move(self):
    # calcular o displacement
    self.time += 1
    displacement = 1.5 * (self.time**2) + self.speed * self.time
    
    # restringir o movimento
    if displacement > 16:
      displacement = 16
    elif displacement < 0:
      displacement -= 2

    self.y += displacement
    
    # angle do passaro
    if displacement < 0 or self.y < (self.height + 50):
      if self.angle < self.MAXIMUM_ROTATION:
        self.angle = self.MAXIMUM_ROTATION
    else:
      if self.angle > -90:
        self.angle -= self.MAXIMUM_ROTATION
  
  def draw(self, screen):
    # definir qual imagem do passaro vai usar
    self.contagem_imagem += 1

    if self.contagem_imagem < self.ANIMATION_TIME:
      self.imagem = self.IMGS[0]
    elif self.contagem_imagem < self.ANIMATION_TIME*2:
      self.imagem = self.IMGS[1]
    elif self.contagem_imagem < self.ANIMATION_TIME*3:
      self.imagem = self.IMGS[2]
    elif self.contagem_imagem < self.ANIMATION_TIME*4:
      self.imagem = self.IMGS[1]
    elif self.contagem_imagem >= self.ANIMATION_TIME*4 + 1:
      self.imagem = self.IMGS[0]
      self.contagem_imagem = 0

    # se o passaro tiver caindo, eu nao vou bater a asa
    if self.angle <= -80:
      self.imagem = self.IMGS[1]
      self.contagem_imagem = self.ANIMATION_TIME*2

    # draw a imagem
    rotated_image = pygame.transform.rotate(self.imagem, self.angle)
    posicao_centro_imagem = self.imagem.get_rect(topleft=(self.x, self.y)).center
    rectangle = rotated_image.get_rect(center=posicao_centro_imagem)
    screen.blit(rotated_image, rectangle.topleft)

  def get_mask(self):
    return pygame.mask.from_surface(self.imagem)

class Cano():
  DISTANCE = 200
  SPEED = 5

  def __init__(self, x):
    self.x = x
    self.height = 0
    self.posicao_topo = 0
    self.posicao_base = 0
    self.CANO_TOPO = pygame.transform.flip(PIPE_IMAGE, False, True)
    self.CANO_BASE = PIPE_IMAGE
    self.passou = False
    self.definir_height()

  def definir_height(self):
    self.height = random.randrange(50, 350)
    self.posicao_topo = self.height - self.CANO_TOPO.get_height()
    self.posicao_base = self.height + self.DISTANCE

  def move(self):
    self.x -= self.SPEED

  def draw(self, screen):
    screen.blit(self.CANO_TOPO, (self.x, self.posicao_topo))
    screen.blit(self.CANO_BASE, (self.x, self.posicao_base))

  def colidir(self, passaro):
    passaro_mask = passaro.get_mask()
    topo_mask = pygame.mask.from_surface(self.CANO_TOPO)
    base_mask = pygame.mask.from_surface(self.CANO_BASE)

    distancia_topo = (self.x - round(passaro.x), self.posicao_topo - round(passaro.y))
    distancia_base = (self.x - round(passaro.x), self.posicao_base - round(passaro.y))

    topo_ponto_colidiu = passaro_mask.overlap(topo_mask, distancia_topo)
    base_ponto_colidiu = passaro_mask.overlap(base_mask, distancia_base)

    if base_ponto_colidiu or topo_ponto_colidiu:
      return True
    else:
      return False

class Floor():
  SPEED = 5
  WIDTH = FLOOR_IMAGE.get_width()
  IMAGEM = FLOOR_IMAGE

  def __init__(self, y):
    self.y = y
    self.x0 = 0
    self.x1 = self.WIDTH

  def move(self):
    self.x0 -= self.SPEED
    self.x1 -= self.SPEED

    if self.x0 + self.WIDTH < 0:
      self.x0 = self.x1 + self.WIDTH
    if self.x1 + self.WIDTH < 0:
      self.x1 = self.x0 + self.WIDTH

  def draw(self, screen):
    screen.blit(self.IMAGEM, (self.x0, self.y))
    screen.blit(self.IMAGEM, (self.x1, self.y))

def draw_screen(screen, birds, pipes, floor, points):
  screen.blit(BACKGROUND_IMAGE, (0, 0))
  for passaro in birds:
    passaro.draw(screen)
  for cano in pipes:
    cano.draw(screen)

  text = POINTS_FONT.render(f"Pontuação: {points}", 1, (245, 245, 245))
  screen.blit(text, (SCREEN_WIDTH - 10 - text.get_width(), 10))

  if ia_playing:
    text = POINTS_FONT.render(f"Geração: {generation}", 1, (245, 245, 245))
    screen.blit(text, (10, 10))

  floor.draw(screen)
  pygame.display.update()

def main(genomes, config): #fitness function
  global generation
  generation += 1

  networks = []
  list_genomes = []
  birds = []
  if ia_playing:
    for _, genome in genomes:
      network = neat.nn.FeedForwardNetwork.create(genome, config)
      networks.append(network)
      genome.fitness = 0
      list_genomes.append(genome)
      birds.append(Passaro(200, 350))
  else:
    birds = [Passaro(200, 200)]
    
  floor = Floor(630)
  pipes = [Cano(700)]
  screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
  points = 0
  relogio = pygame.time.Clock()

  rodando = True
  while rodando:
    relogio.tick(30)

    # interação com o user
    for evento in pygame.event.get():
      if evento.type == pygame.QUIT:
        rodando = False
        pygame.quit()
        quit()
      if not ia_playing:
        if evento.type == pygame.KEYDOWN:
          if evento.key == pygame.K_SPACE:
            for passaro in birds:
              passaro.jump()
              
    pipe_index = 0
    if len(birds) > 0:
      # descobrir qual cano olhar
      if len(pipes) > 1 and birds[0].x > (pipes[0].x + pipes[0].CANO_TOPO.get_width()):
        pipe_index = 1
    else:
      rodando = False
      break

    # move as coisas
    for i, passaro in enumerate(birds):
      passaro.move()
      if ia_playing:
        # aumentar um pouco a fitness do passaro
        list_genomes[i].fitness += 0.1
        output = networks[i].activate((passaro.y, 
                                    abs(passaro.y - pipes[pipe_index].height), 
                                    abs(passaro.y - pipes[pipe_index].posicao_base)))
        # -1 e 1 -> se o output for > 0.5 então o passaro pula
        if output[0] > 0.5:
          passaro.jump()
    floor.move()

    add_pipe = False
    remove_pipes = []
    for cano in pipes:
      for i, passaro in enumerate(birds):
        if cano.colidir(passaro):
          birds.pop(i)
          if ia_playing:
            list_genomes[i].fitness -= 1
            list_genomes.pop(i)
            networks.pop(i)
        if not cano.passou and passaro.x > cano.x:
          cano.passou = True
          add_pipe = True
      cano.move()
      if cano.x + cano.CANO_TOPO.get_width() < 0:
        remove_pipes.append(cano)

    if add_pipe:
      points += 1
      pipes.append(Cano(600))
      for genome in list_genomes:
        genome.fitness += 5
    for cano in remove_pipes:
      pipes.remove(cano)

    for i, passaro in enumerate(birds):
      if (passaro.y + passaro.imagem.get_height()) > floor.y or passaro.y < 0:
        birds.pop(i)
        if ia_playing:
          list_genomes.pop(i)
          networks.pop(i)

    draw_screen(screen, birds, pipes, floor, points)

def rodar(config_path):
  config = neat.config.Config(neat.DefaultGenome,
                              neat.DefaultReproduction,
                              neat.DefaultSpeciesSet,
                              neat.DefaultStagnation,
                              config_path)
  
  population = neat.Population(config)
  population.add_reporter(neat.StdOutReporter(True))
  population.add_reporter(neat.StatisticsReporter())
  
  if ia_playing:
    population.run(main, 50)
  else:
    main(None, None)
    
if __name__ == "__main__":
  path = os.path.dirname(__file__)
  config_path = os.path.join(path, 'config.txt')
  rodar(config_path)