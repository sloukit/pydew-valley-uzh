import math
import random
from typing import override

import pygame

from src.enums import InventoryResource, Layer
from src.settings import SCALE_FACTOR, Coordinate
from src.sprites.base import Sprite
from src.support import oscilating_lerp, rand_circular_pos
from src.timer import Timer


class DropsManager:
    def __init__(self, all_sprites, drops_group, drop_frames):
        self.all_sprites = all_sprites
        self.drops_group = drops_group
        self.drop_frames = drop_frames

        self.player = None  # must be assigned after the level setup

    def drop(self, pos: Coordinate, drop_type: InventoryResource, amount=1):
        if not self.player:
            return
        for _ in range(amount):
            name = drop_type.as_serialised_string()
            surf = self.drop_frames[name]
            Drop(
                pos,
                surf,
                (self.all_sprites, self.drops_group),
                self.player,
                drop_type,
                name=name + " drop",
            )

    def check_collisions(self):
        if not self.player:
            return
        for drop in self.drops_group:
            if self.player.hitbox_rect.colliderect(drop.hitbox_rect) and drop.on_ground:
                drop.kill()
                sound = random.choice(["pop0", "pop1", "pop2"])
                self.player.add_resource(drop.drop_type, sound=sound)

    def update(self):
        self.check_collisions()


# TODO: find an efficient approach for collisions
# drops shouldnt go into collision sprites
class Drop(Sprite):
    def __init__(self, pos, surf, groups, player, drop_type, name="test"):
        super().__init__(pos, surf, groups, name=name)
        self.hitbox_rect.inflate_ip(
            -surf.get_width() * 0.15 * SCALE_FACTOR,
            -surf.get_height() * 0.15 * SCALE_FACTOR,
        )
        # identity
        self.name = name
        self.drop_type = drop_type

        # drop range
        self.min_radius = 60
        self.max_radius = 130

        # positions
        self.throw_pos = pygame.Vector2(pos)  # this is to save the initial pos
        self.pos = pygame.Vector2(pos)
        # item_pos is the same as pos but will have an offest on the y axies
        self.item_pos = pygame.Vector2(pos)
        self.target_pos = pygame.Vector2(
            rand_circular_pos(pos, self.max_radius, self.min_radius)
        )
        # bounce pos is 70% of the distance to the target pos
        self.bounce_pos = self.item_pos.lerp(self.target_pos, 0.7)

        # speeds
        self.speed = 125
        self.after_bounce_speed = self.speed * 0.4

        # vertiual height
        self.curr_height = 0
        self.max_height = 125
        self.bounce_max_height = self.max_height * 0.35

        # modifying values based on distance
        distance = self.throw_pos.distance_to(self.target_pos)
        limiter = (1 - distance / self.max_radius) * 0.8
        self.max_height -= self.max_height * limiter
        self.bounce_max_height -= self.bounce_max_height * limiter
        self.speed -= self.speed * limiter
        self.after_bounce_speed -= self.after_bounce_speed * limiter

        # state
        self.bounced = False  # will be true after the first bounce
        self.on_ground = False  # will be true after reaching the target_pos
        self.suprise_jump = False

        # timers
        self.suprise_jump_timer = Timer(random.randint(5000, 13000), autostart=True)
        self.jump_dur_timer = Timer(1900)

        # groups
        self.all_sprites = groups[0]  # first group should be all_sprites

        # debug
        self.debug = False

        # shadow
        self.shadow = DropShadow(self)

        # moving toward the player
        self.player = player
        self.pull_radius = 70
        self.pull_speed = 420

        # hovering
        self.hover_height = 13  # resambles a radius
        self.hover_speed = 140  # rate of change in angle
        self.hover_angle = 0  # to make the drop hover on the y axies

    def bounce_to(self, start_pos, target_pos, speed, max_height):
        # calculating stuff
        t = self.pos.distance_to(start_pos) / target_pos.distance_to(start_pos)
        offset = max_height * oscilating_lerp(0, 1, t)
        # moving
        self.pos.move_towards_ip(target_pos, speed)
        self.item_pos.x = self.pos.x
        # offsetting the y to simulate virutal height
        self.item_pos.y = self.pos.y - offset
        # updating the rect
        self.rect.center = self.item_pos
        return bool(int(t))  # 1 = reached goal

    def move(self, dt):
        if not self.bounced:
            # go to bounce position
            self.bounced = self.bounce_to(
                self.throw_pos, self.bounce_pos, self.speed * dt, self.max_height
            )
        elif not self.on_ground:
            # go to target position
            self.on_ground = self.bounce_to(
                self.bounce_pos,
                self.target_pos,
                self.after_bounce_speed * dt,
                self.bounce_max_height,
            )
        else:
            # move toward the player
            target = pygame.Vector2(self.player.hitbox_rect.center)
            distance = target.distance_to(self.pos)
            if distance < self.pull_radius:
                t = (1 - distance / self.pull_radius) ** 1.5  # ease-in
                speed = pygame.math.lerp(0, self.pull_speed, t)
                self.item_pos.move_towards_ip(target, speed * dt)
                # update stuff
                self.rect.center = self.item_pos
                self.pos = self.item_pos

            # hover and suprise_jump
            if not self.suprise_jump:
                height = self.hover_height
                speed = self.hover_speed
            else:
                height = self.hover_height * 4
                speed = self.hover_speed * 1.3

            # hover
            if self.hover_angle <= 180:
                self.hover_angle = self.hover_angle + speed * dt
            else:
                self.hover_angle = 0
            angle = math.sin(math.radians(self.hover_angle))
            self.rect.centery = self.item_pos.y - (angle * height)
            # disable suprise_jump after 1 jump
            if self.hover_angle == 0 and self.suprise_jump:
                self.suprise_jump = False
                self.suprise_jump_timer.duration = random.randint(9000, 19000)
                self.suprise_jump_timer.activate()
        # update hitbox
        self.hitbox_rect.center = self.rect.center

    def collision_check(self):
        pass

    def draw(self, screen: pygame.Surface, rect: pygame.Rect, camera):
        super().draw(screen, rect, camera)
        if not self.debug:
            return
        pygame.draw.circle(
            screen, "cyan", self.throw_pos + rect.topleft, self.max_radius, 1
        )
        pygame.draw.circle(
            screen, "cyan", self.throw_pos + rect.topleft, self.min_radius, 1
        )
        pygame.draw.circle(screen, "brown", self.target_pos + rect.topleft, 3)
        pygame.draw.circle(screen, "red", self.bounce_pos + rect.topleft, 3)
        pygame.draw.circle(screen, "pink", self.item_pos + rect.topleft, 3)
        pygame.draw.rect(screen, "white", (self.hitbox_rect.move(*rect.topleft)), 1)
        pygame.draw.rect(
            screen, "gray", (self.player.hitbox_rect.move(*rect.topleft)), 1
        )
        pygame.draw.circle(screen, "black", self.pos + rect.topleft, 3)
        pygame.draw.circle(
            screen, "yellow", self.player.hitbox_rect.center + rect.topleft, 3
        )
        pygame.draw.circle(
            screen,
            "yellow",
            self.player.hitbox_rect.center + rect.topleft,
            self.pull_radius,
            1,
        )

    @override
    def kill(self):
        super().kill()
        self.shadow.kill()

    def update(self, dt):
        self.move(dt)
        # suprise jump timers
        self.suprise_jump_timer.update()
        self.jump_dur_timer.update()
        if self.suprise_jump_timer.finished and not self.suprise_jump:
            self.suprise_jump = True
            self.jump_dur_timer.activate()
            self.hover_angle = 0


class DropShadow(Sprite):
    def __init__(self, drop: Drop):
        surf = pygame.Surface(
            (drop.rect.width * 0.85, drop.rect.height * 0.55), pygame.SRCALPHA
        )
        surf.set_colorkey((0, 0, 0))
        rect = surf.get_frect(topleft=(0, 0))
        pygame.draw.ellipse(surf, (1, 1, 1, 35), rect)
        super().__init__(drop.pos, surf, groups=(drop.all_sprites,), z=Layer.PLANT)
        self.drop = drop

    def update(self, dt):
        # follow the drop
        self.rect.centerx = self.drop.pos[0]
        self.rect.centery = self.drop.pos[1] + self.drop.rect.width / 2

        # change size depending on how far the drop is from the groud
        dist_from_floor = self.drop.pos.distance_to(self.drop.rect.center)
        max_dist = self.drop.max_height
        normalized_dist = 1 - dist_from_floor / max_dist
        if dist_from_floor <= max_dist:
            width = self.surf.width * normalized_dist
            height = self.surf.height * normalized_dist
            self.image = pygame.transform.scale(self.surf, (width, height))
            self.rect = self.image.get_frect(
                center=(self.drop.pos[0], self.drop.pos[1] + self.drop.rect.width / 2)
            )
