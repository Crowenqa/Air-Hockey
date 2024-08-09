import pygame
import socket
import threading
import sys
import math
import time
from pygame.locals import *

SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345

running = True


w, h = 850, 650
a = 0.98
dt = 0.15

screen = pygame.display.set_mode((w,h))
pygame.init()

redgoals = 0
bluegoals = 0

bg = pygame.image.load("TTT.png")
bg = pygame.transform.scale(bg, (w, h))
pygame.display.set_caption("HLM BD")

white = (255, 255, 255)
rang2 = (193, 35, 30)
rang1 = (32, 86, 123)
line = (255, 158, 45)

clock = pygame.time.Clock()

font = pygame.font.Font('freesansbold.ttf', 32)


turn = 1
stopped = 1
goaled = 0
player = 1

teams = {rang1 : 1, rang2 : 0, white : 3}

players = ["", ""]

def get_username():
    global name
    name = input("Enter your username: ")
    return name

def server_communication(sock):
    global running, BALLS, stopped, goaled, redgoals, bluegoals, players, player, turn

    buffer = ""
    while running:
        try:
            data = sock.recv(1024).decode()
            if not data:
                break
            
            buffer += data
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                if message:
                    print(message)
                    if message.startswith("START"):
                        players = message.split(":")[1].split(",")
                        if players[0] == name:
                            player = 0
                        initialize_game(players)
                    elif message.startswith("BALLS"):
                        ddata = message.split(":")[1].split(";")
                        for i in range(len(ddata)):
                            ddata[i] = ddata[i].split(",")
                            BALLS[i].pos = (float(ddata[i][0]), float(ddata[i][1]))
                            BALLS[i].v = (float(ddata[i][2]), float(ddata[i][3]))
                            BALLS[i].color = (int(ddata[i][4]), int(ddata[i][5]), int(ddata[i][6]))
                            BALLS[i].m = float(ddata[i][7])
                    elif message.startswith("TURN"):
                        turn = int(message.split(":")[1])
                        print(turn)
                    elif message.startswith("STOPPED"):
                        stopped = int(message.split(":")[1])
                    elif message.startswith("GOALED"):
                        goaled = int(message.split(":")[1])
        except ConnectionError:
            break


def draw_glowing_line(surface, color, start_pos, end_pos, width):
    for i in range(1, 10):
        alpha = 255 // (i + 1)
        thick = width + i * 2
        glow_color = (color[0], color[1], color[2], alpha)
        draw_line(surface, glow_color, start_pos, end_pos, thick)

def draw_line(surface, color, start_pos, end_pos, width):
    temp_surface = pygame.Surface((800, 600), pygame.SRCALPHA)
    pygame.draw.line(temp_surface, color, start_pos, end_pos, width)
    surface.blit(temp_surface, (0, 0))

def draw_glowing_circle(surface, color, position, radius, width):
    for i in range(1, 10):
        alpha = 255 // (i + 1)
        thick = width + i * 2
        glow_color = (color[0], color[1], color[2], alpha)
        draw_circle(surface, glow_color, position, radius + i, thick)

def draw_circle(surface, color, position, radius, width):
    temp_surface = pygame.Surface((800, 600), pygame.SRCALPHA)
    pygame.draw.circle(temp_surface, color, position, radius, width)
    surface.blit(temp_surface, (0, 0))

class Ball:
    def __init__(self, pos, r, color, m, image1_path):
        self.pos = pos
        self.r = r
        self.color = color
        self.m = m
        self.v = (0, 0)
        self.select = False
        self.start = (0,0)
        self.image = pygame.image.load(image1_path)
        self.image = pygame.transform.scale(self.image, (2 * self.r, 2 * self.r))
        self.rect = self.image.get_rect(center = self.pos)

    def update(self):
        if self.color == white:
            goal_y_top = h // 3 + 20
            goal_y_bottom = 2 * h // 3 - 20
            if (self.pos[0] - self.r < 45) and ( h // 3 < self.pos[1] and 2 * h // 3 > self.pos[1]):
                return 2
            if (self.pos[0] + self.r > w - 45) and ( h // 3 < self.pos[1] and 2 * h // 3 > self.pos[1]):
                return 1
        if not self.select:
            self.pos = (self.pos[0] + self.v[0] * dt, self.pos[1] + self.v[1] * dt)
            speed = math.sqrt(self.v[0] ** 2 + self.v[1] ** 2)
            if speed != 0:
                AAAAA = a * self.m * dt
                if speed > AAAAA:
                    self.v = (self.v[0] - (self.v[0] / speed) * AAAAA, self.v[1] - (self.v[1] / speed) * AAAAA)
                else:
                    self.v = (0, 0)
            if self.pos[0] - self.r < 30 or self.pos[0] + self.r > w - 30:
                self.v = (-self.v[0], self.v[1])
                self.pos = (max(self.r, min(w - self.r, self.pos[0])), self.pos[1])
            if self.pos[1] - self.r < 90 or self.pos[1] + self.r > h - 90:
                self.v = (self.v[0], -self.v[1])
                self.pos = (self.pos[0], max(self.r, min(h - self.r, self.pos[1])))
        return 0

    def draw(self):
        if self.color == white:
            draw_glowing_circle(screen, (255, 158, 45), self.pos, self.r, 5)
        if self.select:
            draw_glowing_circle(screen, self.color, self.pos, self.r, 5)
            mouse_current_x, mouse_current_y = pygame.mouse.get_pos()
            if (self.pos[0] > mouse_current_x):
                line_x =  self.pos[0] + abs(self.pos[0] - mouse_current_x)
            else:
                line_x = self.pos[0] - abs(self.pos[0] - mouse_current_x)
            if (self.pos[1] > mouse_current_y):
                line_y =  self.pos[1] + abs(self.pos[1] - mouse_current_y)
            else:
                line_y = self.pos[1] - abs(self.pos[1] - mouse_current_y)
            pygame.draw.line(screen, line, self.pos, (line_x, line_y), 4)
        ball_rect = self.image.get_rect(center=self.pos)
        screen.blit(self.image, ball_rect)

    def check(self, other):
        dist = math.sqrt((self.pos[0] - other.pos[0]) ** 2+ (self.pos[1] - other.pos[1]) ** 2)
        return dist < self.r + other.r - 2

    def push(self, other):
        dx, dy = other.pos[0] - self.pos[0], other.pos[1] - self.pos[1]
        dist = math.sqrt(dx ** 2 + dy ** 2)
        theta = math.atan2(dy, dx)

        v1_rot = (self.v[0] * math.cos(theta) + self.v[1] * math.sin(theta), -self.v[0] * math.sin(theta) + self.v[1] * math.cos(theta))
        v2_rot = (other.v[0] * math.cos(theta) + other.v[1] * math.sin(theta), -other.v[0] * math.sin(theta) + other.v[1] * math.cos(theta))

        v1_rot_prime = ((v1_rot[0] * (self.m - other.m) + 2 * other.m * v2_rot[0]) / (self.m + other.m), v1_rot[1])
        v2_rot_prime = ((v2_rot[0] * (other.m - self.m) + 2 * self.m * v1_rot[0]) / (self.m + other.m), v2_rot[1])

        if other.r != 30:
            self.v = (v1_rot_prime[0] * math.cos(theta) - v1_rot_prime[1] * math.sin(theta), v1_rot_prime[0] * math.sin(theta) + v1_rot_prime[1] * math.cos(theta))
        else:
            self.v = ((v1_rot_prime[0] * math.cos(theta) - v1_rot_prime[1] * math.sin(theta)) * 1.2, (v1_rot_prime[0] * math.sin(theta) + v1_rot_prime[1] * math.cos(theta)) * 1.2)
            
        if self.r == 30:
            other.v = (v2_rot_prime[0] * math.cos(theta) - v2_rot_prime[1] * math.sin(theta), v2_rot_prime[0] * math.sin(theta) + v2_rot_prime[1] * math.cos(theta))
        else:
            other.v = ((v2_rot_prime[0] * math.cos(theta) - v2_rot_prime[1] * math.sin(theta)) * 1.2, (v2_rot_prime[0] * math.sin(theta) + v2_rot_prime[1] * math.cos(theta)) * 1.2)

        overlap = self.r + other.r - dist
        
        if overlap > 0:
            correction = overlap / 2
            correction_x = correction * math.cos(theta)
            correction_y = correction * math.sin(theta)
            self.pos = (self.pos[0] - correction_x, self.pos[1] - correction_y)
            other.pos = (other.pos[0] + correction_x, other.pos[1] + correction_y)

    def handle_event(self, stopped, event, sock):
        global player, turn
        if turn == teams[self.color] and stopped and teams[self.color] == player:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if math.sqrt((mouse_x - self.pos[0]) ** 2 + (mouse_y - self.pos[1]) ** 2) <= self.r:
                    self.start = event.pos
                    self.select = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if self.select:
                    mouse_end_x, mouse_end_y = event.pos
                    angle = math.atan2(self.pos[1] - mouse_end_y, self.pos[0] - mouse_end_x)
                    distance = math.sqrt((self.pos[0] - mouse_end_x) ** 2 + (self.pos[1] - mouse_end_y) ** 2)
                    speed = distance * 0.1
                    self.v = (speed * math.cos(angle), speed * math.sin(angle))
                    self.select = False
                    turn = 1 - teams[self.color]
                    send_game_state(sock)

def reset():
    BALLS = []
    BALLS.append(Ball((w - (4 * w // 10),  h // 2), 30, rang1, 3, "YEK.png"))
    BALLS.append(Ball((4 * w // 10,  h // 2), 30, rang2, 3, "DO.png"))
    BALLS.append(Ball((w - 3 * w // 10 + 80, h // 2 + 100), 35, rang1, 3.5, "YEK2.png"))
    BALLS.append(Ball((3 * w // 10 - 80, h // 2 + 100), 35, rang2, 3.5, "DO2.png"))
    BALLS.append(Ball((w - (3 * w // 10) + 80, h //2 - 100), 35, rang1, 3.5, "YEK2.png"))
    BALLS.append(Ball((3 * w // 10 - 80, h // 2 - 100), 35, rang2, 3.5, "DO2.png"))
    BALLS.append(Ball((w - (4 * w // 10) + 80,  h // 2), 30, rang1, 3, "YEK.png"))
    BALLS.append(Ball((4 * w // 10 - 80,  h // 2), 30, rang2, 3, "DO.png"))
    BALLS.append(Ball((w - (2 * w // 10) + 50,  h // 2), 31, rang1, 3, "YEK.png"))
    BALLS.append(Ball((2 * w // 10 - 50,  h // 2), 31, rang2, 3, "DO.png"))
    BALLS.append(Ball((w // 2,  h // 2), 15, white, 2, "SoccerBall.png"))
    return BALLS
BALLS = reset()

def send_game_state(sock):
    global BALLS, turn, stopped, goaled, redgoals, bluegoals
    balls_data = ""
    for ball in BALLS:
        balls_data += f"{ball.pos[0]},{ball.pos[1]},{ball.v[0]},{ball.v[1]},{ball.color[0]},{ball.color[1]},{ball.color[2]},{ball.m};"
    balls_data = balls_data[:-1]
    sock.sendall(f"BALLS:{balls_data}\n".encode())
    sock.sendall(f"TURN:{(turn)}\n".encode())
    sock.sendall(f"STOPPED:{stopped}\n".encode())
    sock.sendall(f"GOALED:{goaled}\n".encode())

def initialize_game(players):
    global BALLS
    

def clear():
    global players, turn, redgoals, bluegoals
    text1 = font.render(players[0] + "'s turn", True, rang1)
    textRect1 = text1.get_rect(center = (w // 2, h // 12))
    text2 = font.render(players[1] + "'s turn", True, rang2)
    textRect2 = text2.get_rect(center = (w // 2, h // 12))
    screen.blit(bg, (0,0))
    counter1 = font.render(str(bluegoals), True, rang1)
    counterRect1 = counter1.get_rect(center = (3 * w // 4, h // 12))
    counter2 = font.render(str(redgoals), True, rang2)
    counterRect2 = counter2.get_rect(center = (w // 4, h // 12))
    screen.blit(counter1, counterRect1)
    screen.blit(counter2, counterRect2)
    if turn == 1:
        screen.blit(text1, textRect1)
    else:
        screen.blit(text2, textRect2)
    for ball in BALLS:
        ball.draw()

def main():

    pygame.display.set_caption("HLM BD")
    clock = pygame.time.Clock()

    username = get_username()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))

    sock.sendall(username.encode())

    threading.Thread(target=server_communication, args=(sock,)).start()

    global running, BALLS, turn, stopped, goaled, redgoals, bluegoals

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            for ball in BALLS:
                ball.handle_event(stopped, event, sock)

        stopped = 1

        for ball in BALLS:
            goaled = ball.update()
            if goaled == 1:
                redgoals += 1
                BALLS = reset()
            elif goaled == 2:
                bluegoals += 1
                BALLS = reset()


        for i in range(len(BALLS)):
            for j in range(i + 1, len(BALLS)):
                if BALLS[i].check(BALLS[j]):
                    BALLS[i].push(BALLS[j])

        for ball in BALLS:
            if ball.v != (0,0):
                stopped = 0

        clear()
        
        if goaled:
            for i in range (1, 9):
                clear()
                goal = pygame.image.load("G" + str(i) +".png")
                goalRect = goal.get_rect(center= (w//2, h//2))
                screen.blit(goal, goalRect)
                pygame.display.flip()
                time.sleep(0.03)
            time.sleep(0.5)

        clear()
        pygame.display.flip()

        if redgoals == 3:
            win = pygame.image.load("win1.png")
            win = pygame.transform.scale(win, (600, 190))
            winRect = goal.get_rect(center= (w//2, h//2))
            screen.blit(win, winRect)
            pygame.display.flip()
            time.sleep(1)
            running = 0
        if bluegoals == 3:
            win = pygame.image.load("win2.png")
            win = pygame.transform.scale(win, (600, 190))
            winRect = win.get_rect(center= (w//2, h//2))
            screen.blit(win, winRect)
            pygame.display.flip()
            time.sleep(1)
            running = 0

        clock.tick(120)

    pygame.quit()
    sock.close()

if __name__ == "__main__":
    main()
