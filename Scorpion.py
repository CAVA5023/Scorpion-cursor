import pygame
import math
import sys

CONFIG = {
    "length": 26,
    "speed": 0.18,
    "theme": "skeletal",
    "themes": {
        "skeletal": {
            "stroke": (255, 255, 255),
            "joints": (220, 220, 220),
            "ribs": (255, 255, 255, 215),
            "bg": (5, 5, 5)
        },
        "cyber": {
            "stroke": (56, 189, 248),
            "joints": (2, 132, 199),
            "ribs": (56, 189, 248, 215),
            "bg": (3, 7, 18)
        },
        "toxic": {
            "stroke": (244, 63, 94),
            "joints": (190, 18, 60),
            "ribs": (244, 63, 94, 215),
            "bg": (9, 3, 4)
        }
    }
}

class InputState:
    def __init__(self):
        self.mouse_x = 400
        self.mouse_y = 300

Input = InputState()

class LimNode:
    def __init__(self, parent=None, length=22):
        self.parent = parent
        self.isSegment = True
        self.length = length
        self.x = parent.x if parent else Input.mouse_x
        self.y = parent.y if parent else Input.mouse_y
        self.angle = 0.0

    def follow(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        self.angle = math.atan2(dy, dx)
        self.x = target_x - math.cos(self.angle) * self.length
        self.y = target_y - math.sin(self.angle) * self.length

class LimSystem:
    def __init__(self, end_node, length, speed, creature):
        self.creature = creature
        self.nodes = []

        node = end_node
        for i in range(length):
            if not node:
                parent_node = self.nodes[-1] if len(self.nodes) > 0 else None
                node = LimNode(parent_node, 22)
            
            self.nodes.insert(0, node)
            node = node.parent
            if node and not getattr(node, "isSegment", False):
                self.length = i + 1
                break

        self.hip = self.nodes[0].parent if self.nodes and self.nodes[0] else None

    def move_to(self, target_x, target_y):
        lead_x = target_x
        lead_y = target_y

        for node in self.nodes:
            node.follow(lead_x, lead_y)
            lead_x = node.x
            lead_y = node.y

    def update(self):
        self.move_to(Input.mouse_x, Input.mouse_y)

class SkeletalScorpion:
    def __init__(self, start_x, start_y):
        self.head_x = start_x
        self.head_y = start_y
        self.leg_phase = 0.0
        self.lim_system = None
        self.rebuild_system()

    def rebuild_system(self):
        current_parent = None
        for i in range(CONFIG["length"]):
            seg_len = 20 if i < 6 else max(9, 18 - (i * 0.35))
            node = LimNode(current_parent, seg_len)
            current_parent = node
        self.lim_system = LimSystem(current_parent, CONFIG["length"], CONFIG["speed"], self)

    def update(self):
        dx = Input.mouse_x - self.head_x
        dy = Input.mouse_y - self.head_y
        dist = math.hypot(dx, dy)

        self.head_x += dx * CONFIG["speed"]
        self.head_y += dy * CONFIG["speed"]

        if dist > 0.2:
            self.leg_phase += min(dist * 0.04, 0.25)

        self.lim_system.move_to(self.head_x, self.head_y)

    def draw(self, surface):
        theme = CONFIG["themes"][CONFIG["theme"]]
        nodes = self.lim_system.nodes
        if not nodes:
            return

        self.draw_legs(surface, nodes, theme)

        for i, node in enumerate(nodes):
            t = i / len(nodes)
            rib_width = (28 - i * 2.8) if i < 7 else max(5.0, 17.0 - (i * 0.5))

            cos_a = math.cos(node.angle)
            sin_a = math.sin(node.angle)

            perp_x = -sin_a
            perp_y = cos_a

            top_rib = (node.x + perp_x * rib_width, node.y + perp_y * rib_width)
            bot_rib = (node.x - perp_x * rib_width, node.y - perp_y * rib_width)

            pygame.draw.aaline(surface, theme["stroke"], (node.x, node.y), top_rib)
            pygame.draw.aaline(surface, theme["stroke"], (node.x, node.y), bot_rib)

            if i < 12:
                inner_top = (node.x - cos_a * 2.5 + perp_x * rib_width * 0.7,
                             node.y - sin_a * 2.5 + perp_y * rib_width * 0.7)
                inner_bot = (node.x - cos_a * 2.5 - perp_x * rib_width * 0.7,
                             node.y - sin_a * 2.5 - perp_y * rib_width * 0.7)
                pygame.draw.aaline(surface, theme["stroke"], (node.x, node.y), inner_top)
                pygame.draw.aaline(surface, theme["stroke"], (node.x, node.y), inner_bot)

            radius = 4 if i == 0 else max(2, int(3.5 - t * 2))
            pygame.draw.circle(surface, theme["stroke"], (int(node.x), int(node.y)), radius)

            if i > 0:
                prev_x = node.x - cos_a * node.length
                prev_y = node.y - sin_a * node.length
                pygame.draw.aaline(surface, theme["stroke"], (node.x, node.y), (prev_x, prev_y))

            if i == len(nodes) - 1:
                bulb_x = node.x - cos_a * 5
                bulb_y = node.y - sin_a * 5
                pygame.draw.circle(surface, theme["stroke"], (int(bulb_x), int(bulb_y)), 4, 1)

                stinger_x = bulb_x - cos_a * 15 - perp_x * 8
                stinger_y = bulb_y - sin_a * 15 - perp_y * 8
                pygame.draw.aaline(surface, theme["stroke"], (bulb_x, bulb_y), (stinger_x, stinger_y))
                pygame.draw.circle(surface, (255, 255, 255), (int(stinger_x), int(stinger_y)), 2)

    def draw_legs(self, surface, nodes, theme):
        for i in range(4):
            node_idx = i + 1
            if node_idx >= len(nodes):
                break

            node = nodes[node_idx]
            for side in [-1, 1]:
                phase_shift = i * 0.75 + (math.pi if side == 1 else 0)
                step = math.sin(self.leg_phase + phase_shift) * 0.25

                angle = node.angle + (side * math.pi) / 2 + step
                seg1_len, seg2_len, seg3_len = 22, 26, 11

                x1 = node.x + math.cos(angle) * seg1_len
                y1 = node.y + math.sin(angle) * seg1_len

                knee_angle = angle + side * 0.65
                x2 = x1 + math.cos(knee_angle) * seg2_len
                y2 = y1 + math.sin(knee_angle) * seg2_len

                tip_angle = knee_angle + side * 0.4
                x3 = x2 + math.cos(tip_angle) * seg3_len
                y3 = y2 + math.sin(tip_angle) * seg3_len

                pygame.draw.aaline(surface, theme["stroke"], (node.x, node.y), (x1, y1))
                pygame.draw.aaline(surface, theme["stroke"], (x1, y1), (x2, y2))
                pygame.draw.aaline(surface, theme["stroke"], (x2, y2), (x3, y3))

                for jx, jy, r in [(x1, y1, 2), (x2, y2, 2), (x3, y3, 1)]:
                    pygame.draw.circle(surface, theme["joints"], (int(jx), int(jy)), r)

        if len(nodes) > 0:
            head = nodes[0]
            for side in [-1, 1]:
                base_angle = head.angle + side * 0.6
                c1_x = head.x + math.cos(base_angle) * 23
                c1_y = head.y + math.sin(base_angle) * 23

                mid_angle = head.angle + side * 0.3
                c2_x = c1_x + math.cos(mid_angle) * 22
                c2_y = c1_y + math.sin(mid_angle) * 22

                claw_angle = head.angle + side * 0.15
                tip_x = c2_x + math.cos(claw_angle) * 19
                tip_y = c2_y + math.sin(claw_angle) * 19

                pygame.draw.aaline(surface, theme["stroke"], (head.x, head.y), (c1_x, c1_y))
                pygame.draw.aaline(surface, theme["stroke"], (c1_x, c1_y), (c2_x, c2_y))

                pygame.draw.aaline(surface, theme["stroke"], (c2_x, c2_y), (tip_x, tip_y))
                inner_tip = (tip_x - side * 4, tip_y + 4)
                pygame.draw.aaline(surface, theme["stroke"], (c2_x, c2_y), inner_tip)

                pygame.draw.circle(surface, theme["joints"], (int(c1_x), int(c1_y)), 3)
                pygame.draw.circle(surface, theme["joints"], (int(c2_x), int(c2_y)), 2)

def main():
    pygame.init()
    screen_width, screen_height = 1000, 700
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    pygame.display.set_caption("Procedural Skeletal Scorpion Cursor")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Inter", 16)

    scorpion = SkeletalScorpion(screen_width // 2, screen_height // 2)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                Input.mouse_x, Input.mouse_y = event.pos
            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    themes = list(CONFIG["themes"].keys())
                    current_idx = themes.index(CONFIG["theme"])
                    CONFIG["theme"] = themes[(current_idx + 1) % len(themes)]

        scorpion.update()

        theme = CONFIG["themes"][CONFIG["theme"]]
        screen.fill(theme["bg"])

        scorpion.draw(screen)

        fps = int(clock.get_fps())
        ui_text = f"FPS: {fps} | Move mouse | Press 'T' for theme [{CONFIG['theme'].upper()}]"
        text_surface = font.render(ui_text, True, (150, 150, 150))
        screen.blit(text_surface, (15, screen_height - 30))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()