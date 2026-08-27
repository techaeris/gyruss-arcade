import pygame
import math
import random
import sys
import struct

pygame.init()

# Setup mixer and procedurally generate retro sound effects
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1)
except Exception:
    # Fallback if audio device is busy or unavailable
    pass

WIDTH, HEIGHT = 800, 800
CENTER = (WIDTH // 2, HEIGHT // 2)
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 50)
MAGENTA = (255, 50, 255)
GRAY = (150, 150, 150)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gyruss: Techaeris Edition")
clock = pygame.time.Clock()

# Procedural Sound Generators
def gen_laser_sound():
    try:
        buf = bytearray()
        duration = 0.12
        samples = int(22050 * duration)
        for i in range(samples):
            t = i / 22050
            freq = 1500 - (1200 * (t / duration))
            val = int(12000 * math.sin(2 * math.pi * freq * t))
            buf.extend(struct.pack('<h', val))
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None

def gen_explosion_sound():
    try:
        buf = bytearray()
        duration = 0.25
        samples = int(22050 * duration)
        for i in range(samples):
            t = i / 22050
            val = int(14000 * random.uniform(-1, 1) * (1 - t / duration))
            buf.extend(struct.pack('<h', val))
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None

def gen_powerup_sound():
    try:
        buf = bytearray()
        duration = 0.35
        samples = int(22050 * duration)
        for i in range(samples):
            t = i / 22050
            freq = 300 + (900 * (t / duration))
            # Create a warbling synth effect
            freq += 50 * math.sin(2 * math.pi * 30 * t)
            val = int(12000 * math.sin(2 * math.pi * freq * t))
            buf.extend(struct.pack('<h', val))
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None

def gen_hurt_sound():
    try:
        buf = bytearray()
        duration = 0.4
        samples = int(22050 * duration)
        for i in range(samples):
            t = i / 22050
            freq = 150 - (100 * (t / duration))
            val = int(16000 * (math.sin(2 * math.pi * freq * t) + random.uniform(-0.3, 0.3)) * (1 - t / duration))
            buf.extend(struct.pack('<h', val))
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None

# Load generated sounds
snd_laser = gen_laser_sound()
snd_explosion = gen_explosion_sound()
snd_powerup = gen_powerup_sound()
snd_hurt = gen_hurt_sound()

def play_sound(snd):
    if snd:
        try:
            snd.play()
        except Exception:
            pass

class Star:
    def __init__(self, intro_mode=False):
        self.reset(intro_mode)
        # Randomize initial distance so stars don't clump at start
        self.distance = random.uniform(10, 500)
        
    def reset(self, intro_mode=False):
        self.angle = random.uniform(0, math.pi * 2)
        self.distance = 1.0
        if intro_mode:
            self.speed = random.uniform(4, 8)
        else:
            self.speed = random.uniform(1, 3)

    def update(self, intro_mode=False):
        # Acceleration to create deep space perspective
        factor = 25.0 if intro_mode else 50.0
        self.distance += self.speed * (self.distance / factor + 0.1)
        if self.distance > 600:
            self.reset(intro_mode)
            
    def draw(self, surface):
        x = CENTER[0] + math.cos(self.angle) * self.distance
        y = CENTER[1] + math.sin(self.angle) * self.distance
        size = min(4, max(1, int(self.distance / 100)))
        pygame.draw.circle(surface, WHITE, (int(x), int(y)), size)

class Player:
    def __init__(self):
        self.angle = math.pi / 2
        self.radius = 350
        self.speed = 0.04
        self.rect = pygame.Rect(0, 0, 30, 30)
        self.double_shot = False
        self.lives = 3
        
    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle += self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle -= self.speed
            
        self.angle %= math.pi * 2
        
        self.x = CENTER[0] + math.cos(self.angle) * self.radius
        self.y = CENTER[1] + math.sin(self.angle) * self.radius
        self.rect.center = (self.x, self.y)
        
    def draw(self, surface):
        tip_r = self.radius - 20
        back_r = self.radius + 15
        
        p1 = (CENTER[0] + math.cos(self.angle) * tip_r,
              CENTER[1] + math.sin(self.angle) * tip_r)
        p2 = (CENTER[0] + math.cos(self.angle - 0.08) * back_r,
              CENTER[1] + math.sin(self.angle - 0.08) * back_r)
        p3 = (CENTER[0] + math.cos(self.angle + 0.08) * back_r,
              CENTER[1] + math.sin(self.angle + 0.08) * back_r)
              
        pygame.draw.polygon(surface, GREEN, [p1, p2, p3])
        engine_r = self.radius + 18
        engine_pos = (CENTER[0] + math.cos(self.angle) * engine_r,
                      CENTER[1] + math.sin(self.angle) * engine_r)
        pygame.draw.circle(surface, YELLOW, (int(engine_pos[0]), int(engine_pos[1])), 4)

class Bullet:
    def __init__(self, angle, is_enemy=False, offset=0):
        self.angle = angle
        self.is_enemy = is_enemy
        if self.is_enemy:
            self.distance = 50
            self.speed = 5
            self.color = RED
            self.radius = 5
        else:
            self.distance = 350
            self.speed = -12
            self.color = YELLOW
            self.radius = 4
        self.active = True
        self.offset = offset

    def update(self):
        self.distance += self.speed
        if self.distance < 0 or self.distance > 450:
            self.active = False
            
    def get_pos(self):
        x = CENTER[0] + math.cos(self.angle) * self.distance - math.sin(self.angle) * self.offset
        y = CENTER[1] + math.sin(self.angle) * self.distance + math.cos(self.angle) * self.offset
        return (x, y)

    def draw(self, surface):
        pos = self.get_pos()
        pygame.draw.circle(surface, self.color, (int(pos[0]), int(pos[1])), self.radius)
        
    def get_rect(self):
        pos = self.get_pos()
        return pygame.Rect(pos[0]-self.radius, pos[1]-self.radius, self.radius*2, self.radius*2)

class Enemy:
    def __init__(self, type_val=0):
        self.distance = 10
        self.angle = random.uniform(0, math.pi*2)
        self.active = True
        self.type = type_val 
        self.shoot_timer = random.randint(60, 180)
        self.spiral_speed = random.choice([-1, 1]) * random.uniform(0.01, 0.03)
        self.outward_speed = random.uniform(0.5, 1.5)
        self.color = BLUE if type_val == 0 else MAGENTA
        
    def update(self):
        self.angle += self.spiral_speed
        self.distance += self.outward_speed * (self.distance / 100.0 + 0.5)
        self.shoot_timer -= 1
        
        if self.distance > 450:
            self.active = False
            
    def get_pos(self):
        x = CENTER[0] + math.cos(self.angle) * self.distance
        y = CENTER[1] + math.sin(self.angle) * self.distance
        return (x, y)
        
    def draw(self, surface):
        pos = self.get_pos()
        size = min(15, max(3, int(self.distance / 20)))
        pygame.draw.circle(surface, self.color, (int(pos[0]), int(pos[1])), size)
        if self.type == 1:
            pygame.draw.circle(surface, WHITE, (int(pos[0]), int(pos[1])), size//2)
        
    def get_rect(self):
        pos = self.get_pos()
        size = min(15, max(3, int(self.distance / 20)))
        return pygame.Rect(pos[0]-size, pos[1]-size, size*2, size*2)

class Asteroid:
    def __init__(self):
        self.distance = 10
        self.angle = random.uniform(0, math.pi*2)
        self.active = True
        self.outward_speed = random.uniform(0.8, 2.0)
        
    def update(self):
        self.distance += self.outward_speed * (self.distance / 80.0 + 0.5)
        if self.distance > 450:
            self.active = False
            
    def get_pos(self):
        x = CENTER[0] + math.cos(self.angle) * self.distance
        y = CENTER[1] + math.sin(self.angle) * self.distance
        return (x, y)
        
    def draw(self, surface):
        pos = self.get_pos()
        size = min(20, max(5, int(self.distance / 15)))
        pygame.draw.circle(surface, GRAY, (int(pos[0]), int(pos[1])), size)
        
    def get_rect(self):
        pos = self.get_pos()
        size = min(20, max(5, int(self.distance / 15)))
        return pygame.Rect(pos[0]-size, pos[1]-size, size*2, size*2)

def main():
    stars = [Star() for _ in range(150)]
    player = Player()
    bullets = []
    enemies = []
    asteroids = []
    
    score = 0
    high_score = 0
    stage = 1
    
    state = "INTRO"
    
    enemy_spawn_timer = 60
    asteroid_spawn_timer = 300
    fire_cooldown = 0
    
    font = pygame.font.SysFont(None, 36)
    large_font = pygame.font.SysFont(None, 72)
    huge_font = pygame.font.SysFont(None, 110)
    
    while True:
        keys = pygame.key.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if state == "INTRO":
                    if event.key == pygame.K_SPACE:
                        state = "PLAYING"
                        # Reset stars to normal speeds
                        for star in stars:
                            star.reset(intro_mode=False)
                        play_sound(snd_powerup)
                        
                elif state == "GAME_OVER":
                    if event.key == pygame.K_r:
                        player = Player()
                        bullets.clear()
                        enemies.clear()
                        asteroids.clear()
                        score = 0
                        stage = 1
                        state = "PLAYING"
                        play_sound(snd_powerup)
                    
        screen.fill(BLACK)
        
        if state == "INTRO":
            # Fast-moving starfield for intro
            for star in stars:
                star.update(intro_mode=True)
                star.draw(screen)
                
            # Dynamic logo colors
            logo_color = (
                int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.003)),
                int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.003 + 2.0)),
                int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.003 + 4.0))
            )
            
            logo_text = huge_font.render("GYRUSS", True, logo_color)
            edition_text = font.render("TECHAERIS EDITION", True, GREEN)
            
            pulse = int(170 + 85 * math.sin(pygame.time.get_ticks() * 0.008))
            start_color = (pulse, pulse, pulse)
            start_text = font.render("PRESS SPACE TO START", True, start_color)
            
            # Simple decorative ring in center
            pygame.draw.circle(screen, BLUE, CENTER, 150, 2)
            pygame.draw.circle(screen, MAGENTA, CENTER, 100, 1)
            
            screen.blit(logo_text, (WIDTH//2 - logo_text.get_width()//2, HEIGHT//2 - 140))
            screen.blit(edition_text, (WIDTH//2 - edition_text.get_width()//2, HEIGHT//2 - 40))
            screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT//2 + 100))
            
        elif state == "PLAYING" or state == "GAME_OVER":
            # Normal starfield
            for star in stars:
                star.update(intro_mode=False)
                star.draw(screen)
                
            if state == "PLAYING":
                player.update(keys)
                
                if fire_cooldown > 0:
                    fire_cooldown -= 1
                    
                if keys[pygame.K_SPACE] and fire_cooldown <= 0:
                    if player.double_shot:
                        bullets.append(Bullet(player.angle, offset=-10))
                        bullets.append(Bullet(player.angle, offset=10))
                    else:
                        bullets.append(Bullet(player.angle))
                    play_sound(snd_laser)
                    fire_cooldown = 15
                    
                enemy_spawn_timer -= 1
                if enemy_spawn_timer <= 0:
                    is_bonus = random.random() < 0.15 
                    enemies.append(Enemy(1 if is_bonus else 0))
                    enemy_spawn_timer = max(20, 60 - stage * 3)
                    
                asteroid_spawn_timer -= 1
                if asteroid_spawn_timer <= 0:
                    asteroids.append(Asteroid())
                    asteroid_spawn_timer = random.randint(200, 500)
                
                for b in bullets: b.update()
                    
                for e in enemies:
                    e.update()
                    if e.shoot_timer <= 0 and e.distance > 80 and e.distance < 280:
                        bullets.append(Bullet(e.angle, is_enemy=True))
                        e.shoot_timer = random.randint(120, 240)
                        
                for a in asteroids: a.update()
                    
                player_bullets = [b for b in bullets if not b.is_enemy]
                enemy_bullets = [b for b in bullets if b.is_enemy]
                
                # Bullet Collisions
                for b in player_bullets:
                    b_rect = b.get_rect()
                    hit = False
                    for e in enemies:
                        if b_rect.colliderect(e.get_rect()):
                            if b in bullets: bullets.remove(b)
                            if e in enemies: enemies.remove(e)
                            score += 500 if e.type == 1 else 100
                            if e.type == 1:
                                player.double_shot = True
                                play_sound(snd_powerup)
                            else:
                                play_sound(snd_explosion)
                            hit = True
                            break
                            
                    if hit: continue
                    
                    for a in asteroids:
                        if b_rect.colliderect(a.get_rect()):
                            if b in bullets: bullets.remove(b)
                            break
                            
                # Player Collisions
                player_rect = player.rect
                for b in enemy_bullets:
                    if player_rect.colliderect(b.get_rect()):
                        if b in bullets: bullets.remove(b)
                        player.lives -= 1
                        player.double_shot = False
                        play_sound(snd_hurt)
                        if player.lives <= 0:
                            state = "GAME_OVER"
                            if score > high_score:
                                high_score = score
                        break
                        
                for e in enemies:
                    if player_rect.colliderect(e.get_rect()):
                        if e in enemies: enemies.remove(e)
                        player.lives -= 1
                        player.double_shot = False
                        play_sound(snd_hurt)
                        if player.lives <= 0:
                            state = "GAME_OVER"
                            if score > high_score:
                                high_score = score
                        break
                        
                for a in asteroids:
                    if player_rect.colliderect(a.get_rect()):
                        if a in asteroids: asteroids.remove(a)
                        player.lives -= 1
                        player.double_shot = False
                        play_sound(snd_hurt)
                        if player.lives <= 0:
                            state = "GAME_OVER"
                            if score > high_score:
                                high_score = score
                        break
                        
                bullets = [b for b in bullets if b.active]
                enemies = [e for e in enemies if e.active]
                asteroids = [a for a in asteroids if a.active]
                
                if score > stage * 2000:
                    stage += 1
                    play_sound(snd_powerup)
                    
            # Draw game objects
            for e in enemies: e.draw(screen)
            for a in asteroids: a.draw(screen)
            for b in bullets: b.draw(screen)
            
            if state == "PLAYING":
                player.draw(screen)
            
            # HUD
            score_text = font.render(f"SCORE: {score}", True, WHITE)
            screen.blit(score_text, (20, 20))
            
            hi_score_text = font.render(f"HI-SCORE: {high_score}", True, WHITE)
            screen.blit(hi_score_text, (20, 50))
            
            lives_text = font.render(f"LIVES: {player.lives}", True, WHITE)
            screen.blit(lives_text, (WIDTH - 150, 20))
            
            stage_text = font.render(f"WARP: {stage}", True, WHITE)
            screen.blit(stage_text, (WIDTH - 150, 50))
            
            if state == "GAME_OVER":
                game_over_text = large_font.render("GAME OVER", True, RED)
                restart_text = font.render("Press 'R' to Restart", True, WHITE)
                screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 50))
                screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 50))
            
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()