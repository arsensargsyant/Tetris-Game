import pygame
import random
import time
import math
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Game constants
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
PREVIEW_SIZE = 4

# Window dimensions
WINDOW_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 8)  # Extra space for UI
WINDOW_HEIGHT = BLOCK_SIZE * GRID_HEIGHT + 100

# Tetromino shapes
TETROMINOS = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]]   # Z
]

TETROMINO_COLORS = [CYAN, YELLOW, MAGENTA, ORANGE, BLUE, GREEN, RED]

class Tetromino:
    def __init__(self, x: int, y: int, shape_idx: int):
        self.x = x
        self.y = y
        self.shape = TETROMINOS[shape_idx]
        self.color = TETROMINO_COLORS[shape_idx]
        self.rotation = 0
    
    def rotate(self):
        """Rotate the tetromino 90 degrees clockwise"""
        rows = len(self.shape)
        cols = len(self.shape[0])
        rotated = [[0 for _ in range(rows)] for _ in range(cols)]
        
        for r in range(rows):
            for c in range(cols):
                rotated[c][rows - 1 - r] = self.shape[r][c]
        
        self.shape = rotated
    
    def get_positions(self) -> List[Tuple[int, int]]:
        """Get all block positions of the tetromino"""
        positions = []
        for r in range(len(self.shape)):
            for c in range(len(self.shape[0])):
                if self.shape[r][c]:
                    positions.append((self.x + c, self.y + r))
        return positions

class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        

        
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = None
        self.next_piece = None
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        
        self.fall_time = 0
        self.fall_speed = 1000  # milliseconds
        self.random_block_time = 0
        self.random_block_interval = random.randint(15000, 30000)  # Random interval between 15-30 seconds
        self.random_blocks_enabled = False  # Set to False to disable random blocks by default
        
        # Line clearing animation
        self.lines_clearing = []
        self.clear_animation_time = 0
        self.clear_animation_duration = 800  # milliseconds - increased for more visible effect
        
        # Particle effects
        self.particles = []
        
        self.spawn_new_piece()
        self.spawn_new_piece()  # Set next piece
    
    def spawn_new_piece(self):
        """Spawn a new tetromino"""
        if self.next_piece is None:
            shape_idx = random.randint(0, len(TETROMINOS) - 1)
            self.next_piece = Tetromino(GRID_WIDTH // 2 - 1, 0, shape_idx)
        else:
            self.current_piece = self.next_piece
            shape_idx = random.randint(0, len(TETROMINOS) - 1)
            self.next_piece = Tetromino(GRID_WIDTH // 2 - 1, 0, shape_idx)
            
            # Check if new piece can be placed (game over condition)
            if not self.is_valid_position(self.current_piece):
                self.game_over = True
    
    def is_valid_position(self, piece: Tetromino) -> bool:
        """Check if a piece position is valid"""
        for x, y in piece.get_positions():
            if (x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT or 
                (y >= 0 and self.grid[y][x])):
                return False
        return True
    
    def place_piece(self):
        """Place the current piece on the grid"""
        for x, y in self.current_piece.get_positions():
            if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
                self.grid[y][x] = self.current_piece.color
        
        self.clear_lines()
        self.spawn_new_piece()
    
    def clear_lines(self):
        """Clear completed lines and update score"""
        lines_to_clear = []
        for y in range(GRID_HEIGHT):
            if all(self.grid[y]):
                lines_to_clear.append(y)
        
        if lines_to_clear:
            # Start animation instead of immediately clearing
            self.lines_clearing = lines_to_clear.copy()
            self.clear_animation_time = 0
        else:
            # No lines to clear, proceed normally
            self.finish_line_clear()
    
    def finish_line_clear(self):
        """Finish the line clearing process after animation"""
        if not self.lines_clearing:
            return
            
        # Actually clear the lines
        for y in sorted(self.lines_clearing, reverse=True):
            del self.grid[y]
            self.grid.insert(0, [0 for _ in range(GRID_WIDTH)])
        
        # Update score and level
        lines_count = len(self.lines_clearing)
        self.lines_cleared += lines_count
        self.score += lines_count * 100 * self.level
        self.level = self.lines_cleared // 10 + 1
        self.fall_speed = max(100, 1000 - (self.level - 1) * 100)
        
        # Create enhanced particle effects for cleared lines
        grid_x, grid_y = 50, 50  # Same as in draw method
        for y in self.lines_clearing:
            for x in range(GRID_WIDTH):
                if random.random() < 0.5:  # 50% chance for each block to create particles
                    for _ in range(5):  # 5 particles per block
                        particle = {
                            'x': grid_x + x * BLOCK_SIZE + BLOCK_SIZE // 2,
                            'y': grid_y + y * BLOCK_SIZE + BLOCK_SIZE // 2,
                            'vx': random.uniform(-5, 5),
                            'vy': random.uniform(-8, -2),
                            'life': 1.0,
                            'color': random.choice(TETROMINO_COLORS),
                            'size': random.randint(3, 8)  # Variable particle sizes
                        }
                        self.particles.append(particle)
        
        # Reset animation
        self.lines_clearing = []
        self.clear_animation_time = 0
    
    def move_piece(self, dx: int, dy: int) -> bool:
        """Move the current piece and return success status"""
        if self.current_piece is None:
            return False
        
        old_x, old_y = self.current_piece.x, self.current_piece.y
        self.current_piece.x += dx
        self.current_piece.y += dy
        
        if not self.is_valid_position(self.current_piece):
            self.current_piece.x, self.current_piece.y = old_x, old_y
            if dy > 0:  # Moving down failed, place the piece
                self.place_piece()
            return False
        return True
    
    def rotate_piece(self):
        """Rotate the current piece"""
        if self.current_piece is None:
            return
        
        old_shape = self.current_piece.shape
        self.current_piece.rotate()
        
        if not self.is_valid_position(self.current_piece):
            self.current_piece.shape = old_shape
    
    def hard_drop(self):
        """Drop the piece all the way down"""
        while self.move_piece(0, 1):
            pass
    
    def spawn_random_block(self):
        """Spawn a random block on the grid"""
        # Find valid positions (only at bottom or on top of existing blocks)
        valid_positions = []
        
        for x in range(GRID_WIDTH):
            # Find the highest block in this column
            highest_block_y = GRID_HEIGHT
            for y in range(GRID_HEIGHT):
                if self.grid[y][x] != 0:
                    highest_block_y = y
                    break
            
            # Add position above the highest block (or at bottom if column is empty)
            if highest_block_y > 0:
                valid_positions.append((x, highest_block_y - 1))
        
        if valid_positions:
            # Choose random position and color
            x, y = random.choice(valid_positions)
            color = random.choice(TETROMINO_COLORS)
            self.grid[y][x] = color
    
    def update(self, dt: float):
        """Update game state"""
        if self.game_over or self.paused:
            return
        
        self.fall_time += dt
        if self.fall_time >= self.fall_speed:
            self.move_piece(0, 1)
            self.fall_time = 0
        
        # Handle line clearing animation
        if self.lines_clearing:
            self.clear_animation_time += dt
            if self.clear_animation_time >= self.clear_animation_duration:
                self.finish_line_clear()
        
        # Update particles
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.2  # Gravity
            particle['life'] -= 0.02  # Fade out
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Spawn random blocks (only if enabled)
        if self.random_blocks_enabled:
            self.random_block_time += dt
            if self.random_block_time >= self.random_block_interval:
                self.spawn_random_block()
                self.random_block_time = 0
                # Set new random interval for next spawn
                self.random_block_interval = random.randint(15000, 30000)
    
    def draw(self):
        """Draw the game"""
        self.screen.fill(BLACK)
        
        # Draw grid background
        grid_x = 50
        grid_y = 50
        pygame.draw.rect(self.screen, GRAY, 
                        (grid_x - 2, grid_y - 2, 
                         GRID_WIDTH * BLOCK_SIZE + 4, 
                         GRID_HEIGHT * BLOCK_SIZE + 4), 2)
        
        # Draw background grid lines
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(self.screen, (40, 40, 40), 
                           (grid_x + x * BLOCK_SIZE, grid_y), 
                           (grid_x + x * BLOCK_SIZE, grid_y + GRID_HEIGHT * BLOCK_SIZE))
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(self.screen, (40, 40, 40), 
                           (grid_x, grid_y + y * BLOCK_SIZE), 
                           (grid_x + GRID_WIDTH * BLOCK_SIZE, grid_y + y * BLOCK_SIZE))
        
        # Draw placed blocks
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x]:
                    # Check if this line is being cleared
                    is_clearing = y in self.lines_clearing
                    
                    # Calculate animation effects
                    if is_clearing:
                        # Enhanced flashing effect during clear animation
                        progress = self.clear_animation_time / self.clear_animation_duration
                        
                        # Multi-color flashing effect
                        if progress < 0.3:
                            flash_color = (255, 255, 255)  # White flash
                        elif progress < 0.6:
                            flash_color = (255, 255, 0)    # Yellow flash
                        else:
                            flash_color = (255, 0, 0)      # Red flash
                        
                        # Pulsing effect
                        pulse = abs(math.sin(progress * 20))  # Fast pulsing
                        flash_alpha = int(255 * pulse)
                        
                        # Draw the main block
                        pygame.draw.rect(self.screen, self.grid[y][x],
                                       (grid_x + x * BLOCK_SIZE, 
                                        grid_y + y * BLOCK_SIZE,
                                        BLOCK_SIZE, BLOCK_SIZE))
                        
                        # Draw enhanced flashing overlay
                        flash_surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
                        flash_surface.fill(flash_color)
                        flash_surface.set_alpha(flash_alpha)
                        self.screen.blit(flash_surface, (grid_x + x * BLOCK_SIZE, grid_y + y * BLOCK_SIZE))
                        
                        # Add glow effect
                        glow_size = int(BLOCK_SIZE * (1 + pulse * 0.3))
                        glow_surface = pygame.Surface((glow_size, glow_size))
                        glow_surface.fill(flash_color)
                        glow_surface.set_alpha(flash_alpha // 3)
                        glow_x = grid_x + x * BLOCK_SIZE - (glow_size - BLOCK_SIZE) // 2
                        glow_y = grid_y + y * BLOCK_SIZE - (glow_size - BLOCK_SIZE) // 2
                        self.screen.blit(glow_surface, (glow_x, glow_y))
                    else:
                        # Normal block drawing
                        pygame.draw.rect(self.screen, self.grid[y][x],
                                       (grid_x + x * BLOCK_SIZE, 
                                        grid_y + y * BLOCK_SIZE,
                                        BLOCK_SIZE, BLOCK_SIZE))
                    
                    # Draw block border
                    pygame.draw.rect(self.screen, WHITE,
                                   (grid_x + x * BLOCK_SIZE, 
                                    grid_y + y * BLOCK_SIZE,
                                    BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Draw current piece
        if self.current_piece:
            for x, y in self.current_piece.get_positions():
                if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
                    pygame.draw.rect(self.screen, self.current_piece.color,
                                   (grid_x + x * BLOCK_SIZE, 
                                    grid_y + y * BLOCK_SIZE,
                                    BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(self.screen, WHITE,
                                   (grid_x + x * BLOCK_SIZE, 
                                    grid_y + y * BLOCK_SIZE,
                                    BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Draw enhanced particles
        for particle in self.particles:
            alpha = int(255 * particle['life'])
            size = particle.get('size', 4)  # Default size if not set
            particle_surface = pygame.Surface((size, size))
            particle_surface.fill(particle['color'])
            particle_surface.set_alpha(alpha)
            self.screen.blit(particle_surface, (particle['x'] - size//2, particle['y'] - size//2))
        
        # Draw UI
        ui_x = grid_x + GRID_WIDTH * BLOCK_SIZE + 20
        
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (ui_x, 50))
        
        # Level
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_text, (ui_x, 100))
        
        # Lines
        lines_text = self.font.render(f"Lines: {self.lines_cleared}", True, WHITE)
        self.screen.blit(lines_text, (ui_x, 150))
        
        # Next piece preview
        next_text = self.font.render("Next:", True, WHITE)
        self.screen.blit(next_text, (ui_x, 200))
        
        if self.next_piece:
            preview_x = ui_x + 20
            preview_y = 250
            for r in range(len(self.next_piece.shape)):
                for c in range(len(self.next_piece.shape[0])):
                    if self.next_piece.shape[r][c]:
                        pygame.draw.rect(self.screen, self.next_piece.color,
                                       (preview_x + c * BLOCK_SIZE, 
                                        preview_y + r * BLOCK_SIZE,
                                        BLOCK_SIZE, BLOCK_SIZE))
                        pygame.draw.rect(self.screen, WHITE,
                                       (preview_x + c * BLOCK_SIZE, 
                                        preview_y + r * BLOCK_SIZE,
                                        BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Controls info
        controls_y = 400
        
        # Draw controls title
        controls_title = self.font.render("Controls:", True, WHITE)
        self.screen.blit(controls_title, (ui_x, controls_y))
        
        # Draw arrow controls with visual arrows
        arrow_controls = [
            ("Move Left/Right", "←", "→"),
            ("Soft Drop", "↓", ""),
            ("Rotate", "↑", ""),
            ("Hard Drop", "Space", ""),  # Changed back to "Space" for proper positioning
            ("Pause", "P", ""),
            ("Random Blocks", "B", ""),
            ("Restart", "R", "")
        ]
        
        for i, (action, key1, key2) in enumerate(arrow_controls):
            y_pos = controls_y + 40 + i * 22  # Even more compact spacing
            
            # Draw action text
            action_text = self.small_font.render(action, True, GRAY)
            self.screen.blit(action_text, (ui_x, y_pos))
            
            # Draw key/arrow
            if key1 in ["←", "→", "↑", "↓"]:
                # Draw arrow symbol
                arrow_color = WHITE
                arrow_size = 8  # Even smaller arrows
                arrow_x = ui_x + 140  # Moved closer to text
                arrow_y = y_pos + 8
                
                if key1 == "←":
                    # Left arrow
                    pygame.draw.polygon(self.screen, arrow_color, [
                        (arrow_x + arrow_size, arrow_y),
                        (arrow_x, arrow_y + arrow_size//2),
                        (arrow_x + arrow_size, arrow_y + arrow_size)
                    ])
                elif key1 == "→":
                    # Right arrow
                    pygame.draw.polygon(self.screen, arrow_color, [
                        (arrow_x, arrow_y),
                        (arrow_x + arrow_size, arrow_y + arrow_size//2),
                        (arrow_x, arrow_y + arrow_size)
                    ])
                elif key1 == "↑":
                    # Up arrow
                    pygame.draw.polygon(self.screen, arrow_color, [
                        (arrow_x, arrow_y + arrow_size),
                        (arrow_x + arrow_size//2, arrow_y),
                        (arrow_x + arrow_size, arrow_y + arrow_size)
                    ])
                elif key1 == "↓":
                    # Down arrow
                    pygame.draw.polygon(self.screen, arrow_color, [
                        (arrow_x, arrow_y),
                        (arrow_x + arrow_size//2, arrow_y + arrow_size),
                        (arrow_x + arrow_size, arrow_y)
                    ])
                
                # Draw second arrow if needed (for left/right)
                if key2 in ["←", "→", "↑", "↓"]:
                    arrow_x2 = arrow_x + 15  # Even tighter spacing
                    if key2 == "→":
                        pygame.draw.polygon(self.screen, arrow_color, [
                            (arrow_x2, arrow_y),
                            (arrow_x2 + arrow_size, arrow_y + arrow_size//2),
                            (arrow_x2, arrow_y + arrow_size)
                        ])
            else:
                # Draw regular key text
                key_text = self.small_font.render(key1, True, WHITE)
                # Position "Space" further left, other keys closer to arrows
                if key1 == "Space":
                    key_x = ui_x + 120  # Much further left for "Space"
                else:
                    key_x = ui_x + 140  # Normal position for P, B, R
                self.screen.blit(key_text, (key_x, y_pos))
        
        # Random block status and timer
        if self.random_blocks_enabled:
            time_until_random = max(0, (self.random_block_interval - self.random_block_time) / 1000)
            random_text = self.small_font.render(f"Random block in: {time_until_random:.1f}s", True, YELLOW)
        else:
            random_text = self.small_font.render("Random blocks: OFF", True, RED)
        self.screen.blit(random_text, (ui_x, controls_y + 200))
        
        # Game over or pause overlay
        if self.game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.font.render("GAME OVER", True, RED)
            restart_text = self.small_font.render("Press R to restart", True, WHITE)
            
            self.screen.blit(game_over_text, 
                           (WINDOW_WIDTH // 2 - game_over_text.get_width() // 2, 
                            WINDOW_HEIGHT // 2 - 50))
            self.screen.blit(restart_text, 
                           (WINDOW_WIDTH // 2 - restart_text.get_width() // 2, 
                            WINDOW_HEIGHT // 2))
        
        elif self.paused:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            pause_text = self.font.render("PAUSED", True, YELLOW)
            self.screen.blit(pause_text, 
                           (WINDOW_WIDTH // 2 - pause_text.get_width() // 2, 
                            WINDOW_HEIGHT // 2))
        
        pygame.display.flip()
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.__init__()  # Restart game anytime R is pressed
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_b:
                    self.random_blocks_enabled = not self.random_blocks_enabled
                elif not self.game_over and not self.paused:
                    if event.key == pygame.K_LEFT:
                        self.move_piece(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.move_piece(1, 0)
                    elif event.key == pygame.K_DOWN:
                        self.move_piece(0, 1)
                    elif event.key == pygame.K_UP:
                        self.rotate_piece()
                    elif event.key == pygame.K_SPACE:
                        self.hard_drop()
        
        return True
    
    def run(self):
        """Main game loop"""
        running = True
        last_time = time.time()
        
        while running:
            current_time = time.time()
            dt = (current_time - last_time) * 1000  # Convert to milliseconds
            last_time = current_time
            
            running = self.handle_events()
            self.update(dt)
            self.draw()
            
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    game = TetrisGame()
    game.run()
