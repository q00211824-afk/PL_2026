import pygame
from pygame.draw import *
from random import randint, uniform
import math

# Инициализация Pygame
pygame.init()

# Константы экрана
WIDTH = 1200
HEIGHT = 900
FPS = 60

# Цвета
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
MAGENTA = (255, 0, 255)
CYAN = (0, 255, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
COLORS = [RED, BLUE, YELLOW, GREEN, MAGENTA, CYAN]

# Настройки игры
INITIAL_BALLS_PER_LEVEL = [2, 4, 6, 8, 10]          # количество шаров в начале уровня (1-5)
SCORE_PER_HIT = 10                                  # базовые очки за попадание
SCORE_TO_NEXT_LEVEL = [50, 100, 150, 200, 250]     # очки для перехода на след. уровень
TIMEOUT_PER_LEVEL = [10000, 8000, 6000, 4000, 2000]  # таймаут без попаданий (мс)
MAX_BALLS_MULTIPLIER = 5                           # максимальное число шаров = n * MAX_BALLS_MULTIPLIER (из формулы n+2*(n+n)=5n)
MAX_SPEED = 7                                      # максимальная скорость шара (пикселей/кадр)

# Класс шарика
class Ball:
    """Класс, представляющий движущийся шарик"""
    def __init__(self, x, y, radius, color, vx, vy):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.vx = vx
        self.vy = vy

    def update(self, width, height):
        """Обновляет позицию шарика, отражает от стен и ограничивает скорость"""
        self.x += self.vx
        self.y += self.vy
        # Отражение от вертикальных стен
        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = -self.vx
        elif self.x + self.radius >= width:
            self.x = width - self.radius
            self.vx = -self.vx
        # Отражение от горизонтальных стен
        if self.y - self.radius <= 0:
            self.y = self.radius
            self.vy = -self.vy
        elif self.y + self.radius >= height:
            self.y = height - self.radius
            self.vy = -self.vy

        # Ограничение скорости, чтобы шары не улетали
        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED:
            self.vx = self.vx / speed * MAX_SPEED
            self.vy = self.vy / speed * MAX_SPEED

    def draw(self, screen):
        """Рисует шарик на экране"""
        circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def is_point_inside(self, px, py):
        """Проверяет, находится ли точка (px, py) внутри шарика"""
        return math.hypot(px - self.x, py - self.y) <= self.radius

def resolve_collision(b1, b2):
    """
    Решает упругое столкновение двух шаров одинаковой массы.
    Меняет скорости b1 и b2 в соответствии с законами сохранения.
    Также раздвигает шары, чтобы они не перекрывались.
    """
    # Сначала раздвигаем шары, чтобы они не пересекались
    dx = b1.x - b2.x
    dy = b1.y - b2.y
    dist = math.hypot(dx, dy)
    min_dist = b1.radius + b2.radius
    if dist < min_dist and dist != 0:
        overlap = min_dist - dist
        # Нормаль от b2 к b1
        nx = dx / dist
        ny = dy / dist
        # Сдвигаем шары пропорционально (чтобы не зациклить)
        shift = overlap / 2
        b1.x += nx * shift
        b1.y += ny * shift
        b2.x -= nx * shift
        b2.y -= ny * shift
        # Пересчитываем дистанцию (на всякий случай)
        dx = b1.x - b2.x
        dy = b1.y - b2.y
        dist = math.hypot(dx, dy)

    # Теперь разрешаем столкновение по скоростям
    if dist == 0:
        return
    # Нормаль столкновения
    nx = dx / dist
    ny = dy / dist
    # Относительная скорость вдоль нормали
    dvx = b1.vx - b2.vx
    dvy = b1.vy - b2.vy
    vrel = dvx * nx + dvy * ny
    # Если шары уже разлетаются, не обрабатываем
    if vrel > 0:
        return
    # Импульс (массы одинаковы, коэффициент восстановления 1)
    impulse = 2 * vrel
    # Изменение скоростей
    b1.vx -= impulse * nx
    b1.vy -= impulse * ny
    b2.vx += impulse * nx
    b2.vy += impulse * ny

    # Ограничиваем скорости после столкновения
    for ball in (b1, b2):
        speed = math.hypot(ball.vx, ball.vy)
        if speed > MAX_SPEED:
            ball.vx = ball.vx / speed * MAX_SPEED
            ball.vy = ball.vy / speed * MAX_SPEED

def check_collision_with_balls(new_ball, balls):
    """Проверяет, пересекается ли новый шар с уже существующими"""
    for b in balls:
        if math.hypot(new_ball.x - b.x, new_ball.y - b.y) < new_ball.radius + b.radius:
            return True
    return False

def generate_ball(level, balls, width, height, min_radius=20, max_radius=40):
    """
    Генерирует новый шар с параметрами, соответствующими уровню,
    и гарантирует, что он не пересекается с уже существующими.
    Возвращает объект Ball или None, если не удалось подобрать место (практически всегда подбирает).
    """
    # Базовая скорость зависит от уровня (чем выше уровень, тем быстрее, но плавно)
    base_speed = 2 + (level - 1) * 0.5
    # Пытаемся найти свободное место (до 1000 попыток)
    for _ in range(1000):
        radius = randint(min_radius, max_radius)
        x = randint(radius, width - radius)
        y = randint(radius, height - radius)
        # Случайное направление скорости
        angle = uniform(0, 2 * math.pi)
        vx = base_speed * math.cos(angle) + uniform(-1, 1)
        vy = base_speed * math.sin(angle) + uniform(-1, 1)
        # Ограничиваем скорость, чтобы не превышать MAX_SPEED
        speed = math.hypot(vx, vy)
        if speed > MAX_SPEED:
            vx = vx / speed * MAX_SPEED
            vy = vy / speed * MAX_SPEED
        color = COLORS[randint(0, len(COLORS) - 1)]
        ball = Ball(x, y, radius, color, vx, vy)
        if not check_collision_with_balls(ball, balls):
            return ball
    # Если не удалось подобрать (маловероятно), возвращаем шар в центре с минимальным радиусом
    return Ball(width // 2, height // 2, min_radius, COLORS[0], base_speed, base_speed)

def create_initial_balls(level, count, width, height):
    """Создаёт заданное количество шаров для начала уровня"""
    balls = []
    for _ in range(count):
        ball = generate_ball(level, balls, width, height)
        balls.append(ball)
    return balls

def get_combo_multiplier(combo):
    """Возвращает множитель очков в зависимости от текущего комбо"""
    if combo < 2:
        return 1
    elif combo <= 3:
        return 2
    elif combo <= 6:
        return 3
    elif combo <= 9:
        return 5
    else:
        return 10

def draw_text(screen, text, x, y, color=WHITE, size=24):
    """Выводит текст на экран"""
    font = pygame.font.Font(None, size)
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Шарики — игра с уровнями")
    clock = pygame.time.Clock()

    # Переменные игры
    current_level = 1                # текущий уровень (1-5)
    score = 0                        # общее количество очков
    combo_counter = 0                # счётчик попаданий подряд (без промахов)
    last_hit_time = pygame.time.get_ticks()  # время последнего попадания (для таймера)

    # Список шаров
    balls = []

    # Начальные параметры уровня
    level_balls = INITIAL_BALLS_PER_LEVEL[current_level - 1]
    max_balls = level_balls * MAX_BALLS_MULTIPLIER
    score_needed = SCORE_TO_NEXT_LEVEL[current_level - 1]
    timeout_ms = TIMEOUT_PER_LEVEL[current_level - 1]

    # Создаём начальные шары
    balls = create_initial_balls(current_level, level_balls, WIDTH, HEIGHT)

    # Основной игровой цикл
    running = True
    while running:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                hit = False
                # Проверяем, попали ли мы в какой-нибудь шар
                for ball in balls[:]:  # проходим по копии, чтобы можно было удалять
                    if ball.is_point_inside(mx, my):
                        hit = True
                        # Начисляем очки с учётом комбо
                        multiplier = get_combo_multiplier(combo_counter)
                        points = SCORE_PER_HIT * multiplier
                        score += points
                        combo_counter += 1   # увеличиваем комбо
                        last_hit_time = pygame.time.get_ticks()  # обновляем таймер

                        # Удаляем шар
                        balls.remove(ball)

                        # Добавляем два новых шара, если не превышен лимит
                        if len(balls) + 2 <= max_balls:
                            for _ in range(2):
                                new_ball = generate_ball(current_level, balls, WIDTH, HEIGHT)
                                balls.append(new_ball)
                        else:
                            # Если лимит близок, добавляем столько, сколько можно
                            to_add = max_balls - len(balls)
                            for _ in range(to_add):
                                new_ball = generate_ball(current_level, balls, WIDTH, HEIGHT)
                                balls.append(new_ball)
                        break  # после обработки первого попавшего шара выходим из цикла (только один клик за событие)

                # Если не попали ни в один шар — сбрасываем комбо
                if not hit:
                    combo_counter = 0

        # Проверка таймера бездействия (если шары есть)
        if balls:
            elapsed = pygame.time.get_ticks() - last_hit_time
            if elapsed > timeout_ms:
                # Взрываем все шары и создаём заново начальное количество
                balls.clear()
                balls = create_initial_balls(current_level, level_balls, WIDTH, HEIGHT)
                combo_counter = 0
                last_hit_time = pygame.time.get_ticks()   # сброс таймера

        # Обновление движения шаров
        for ball in balls:
            ball.update(WIDTH, HEIGHT)

        # Столкновения между шарами (начиная с 3 уровня)
        if current_level >= 3:
            # Проверяем все пары шаров
            for i in range(len(balls)):
                for j in range(i + 1, len(balls)):
                    b1 = balls[i]
                    b2 = balls[j]
                    # Если шары пересекаются, разрешаем столкновение
                    if math.hypot(b1.x - b2.x, b1.y - b2.y) < b1.radius + b2.radius:
                        resolve_collision(b1, b2)

        # Проверка перехода на следующий уровень
        if score >= score_needed and current_level < 5:
            current_level += 1
            # Обновляем параметры уровня
            level_balls = INITIAL_BALLS_PER_LEVEL[current_level - 1]
            max_balls = level_balls * MAX_BALLS_MULTIPLIER
            score_needed = SCORE_TO_NEXT_LEVEL[current_level - 1]
            timeout_ms = TIMEOUT_PER_LEVEL[current_level - 1]
            # Сбрасываем комбо и таймер
            combo_counter = 0
            last_hit_time = pygame.time.get_ticks()
            # Создаём новый набор шаров для уровня
            balls.clear()
            balls = create_initial_balls(current_level, level_balls, WIDTH, HEIGHT)
            # При переходе также изменяем скорости всех шаров в соответствии с новым уровнем
            base_speed = 2 + (current_level - 1) * 0.5
            for ball in balls:
                # Новая скорость с тем же направлением, но с базовой скоростью уровня
                angle = math.atan2(ball.vy, ball.vx)
                ball.vx = base_speed * math.cos(angle)
                ball.vy = base_speed * math.sin(angle)
                # Ограничиваем скорость
                speed = math.hypot(ball.vx, ball.vy)
                if speed > MAX_SPEED:
                    ball.vx = ball.vx / speed * MAX_SPEED
                    ball.vy = ball.vy / speed * MAX_SPEED
        elif current_level == 5 and score >= score_needed:
            # Победа! Можно завершить игру или вывести поздравление
            draw_text(screen, "ПОБЕДА! ВЫ ПРОШЛИ ВСЕ УРОВНИ!", WIDTH // 2 - 200, HEIGHT // 2, YELLOW, 36)
            pygame.display.update()
            pygame.time.wait(3000)
            running = False

        # Отрисовка
        screen.fill(BLACK)

        # Рисуем все шары
        for ball in balls:
            ball.draw(screen)

        # Вывод информации на экран
        draw_text(screen, f"Уровень: {current_level}", 10, 10, WHITE)
        draw_text(screen, f"Очки: {score}", 10, 40, WHITE)
        draw_text(screen, f"Нужно для след. уровня: {score_needed}", 10, 70, WHITE)
        draw_text(screen, f"Комбо: x{get_combo_multiplier(combo_counter)} ({combo_counter})", 10, 100, WHITE)
        draw_text(screen, f"Шаров на экране: {len(balls)} / {max_balls}", 10, 130, WHITE)

        # Таймер до взрыва (если шары есть)
        if balls:
            remaining = max(0, timeout_ms - (pygame.time.get_ticks() - last_hit_time))
            seconds = remaining // 1000
            millis = (remaining % 1000) // 100
            draw_text(screen, f"До взрыва: {seconds}.{millis} с", 10, 160, WHITE)

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()