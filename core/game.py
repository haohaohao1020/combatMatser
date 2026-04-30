import pygame
import sys
from typing import Optional, List, Tuple

from config import (
    GameState, CharacterState,
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GROUND_Y,
    PLAYER_WIDTH, PLAYER_HEIGHT, ROUND_TIME, MAX_ROUNDS,
    clamp, WHITE, BLACK,
    ENDLESS_WAVE_HEAL_AMOUNT, ENDLESS_WAVE_TRANSITION_FRAMES
)
from characters import Character, AIController, add_ai_to_character
from characters.hero_system import HeroCharacter, HeroType, create_hero, get_all_hero_types
from attacks import get_light_attack, get_heavy_attack, get_low_attack
from effects import EffectManager, ScreenShake
from ui import UI, InGameMenu
from menus import MainMenu, HeroSelectMenu
from stage import Stage
from core.endless_mode import EndlessModeManager


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Combat Master - 格斗大师")
        self.clock = pygame.time.Clock()
        self.running = True

        self.state = GameState.MENU
        self.game_mode = "pvp"
        self.difficulty = "easy"

        self.round_timer = ROUND_TIME
        self.round_timer_frames = 0
        self.p1_wins = 0
        self.p2_wins = 0
        self.current_round = 1

        self.round_transition = False
        self.round_transition_timer = 0
        self.round_transition_text = ""

        self.player1_hero_type: Optional[HeroType] = HeroType.BASIC_FIGHTER
        self.player2_hero_type: Optional[HeroType] = HeroType.BASIC_FIGHTER
        self.use_hero_system = True
        self._pending_mode: str = "normal"

        self.player1: Optional[HeroCharacter] = None
        self.player2: Optional[HeroCharacter] = None
        self.ai_controller: Optional[AIController] = None
        self.stage = Stage()
        self.effect_manager = EffectManager()
        self.screen_shake = ScreenShake()

        self.endless_manager: Optional[EndlessModeManager] = None

        self.ui = UI()
        self.main_menu = MainMenu()
        self.hero_select_menu = HeroSelectMenu()
        self.ingame_menu = InGameMenu()

        self.ui.init_fonts()
        self.main_menu.init_fonts()
        self.hero_select_menu.init_fonts()
        self.ingame_menu.init_fonts()

        self.main_menu.set_menu("main")

    def start_new_round(self):
        ground_y = GROUND_Y - PLAYER_HEIGHT

        if self.use_hero_system and self.player1_hero_type and self.player2_hero_type:
            self.player1 = create_hero(200, ground_y, is_player1=True, hero_type=self.player1_hero_type)
            self.player2 = create_hero(SCREEN_WIDTH - 260, ground_y, is_player1=False, hero_type=self.player2_hero_type)
        else:
            self.player1 = Character(200, ground_y, is_player1=True)
            self.player2 = Character(SCREEN_WIDTH - 260, ground_y, is_player1=False)

        if self.game_mode == "pvc":
            self.ai_controller = add_ai_to_character(self.player2, self.difficulty)
        else:
            self.ai_controller = None

        self.round_timer = ROUND_TIME
        self.round_timer_frames = 0
        self.effect_manager.clear()
        self.screen_shake = ScreenShake()

        self.round_transition = True
        self.round_transition_timer = 120
        self.round_transition_text = f"ROUND {self.current_round}"

    def start_game(self):
        self.current_round = 1
        self.p1_wins = 0
        self.p2_wins = 0
        self.hero_select_menu.reset_selection()
        self.state = GameState.HERO_SELECT

    def start_game_after_hero_select(self):
        self.current_round = 1
        self.p1_wins = 0
        self.p2_wins = 0
        self.start_new_round()
        self.state = GameState.PLAYING

    def start_endless_mode(self):
        self.endless_manager = EndlessModeManager()

        ground_y = GROUND_Y - PLAYER_HEIGHT
        if self.use_hero_system and self.player1_hero_type:
            self.player1 = create_hero(SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2, ground_y,
                                       is_player1=True, hero_type=self.player1_hero_type)
        else:
            self.player1 = Character(SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2, ground_y, is_player1=True)

        self.player2 = None
        self.ai_controller = None

        self.effect_manager.clear()
        self.screen_shake = ScreenShake()

        self.endless_manager.start(self.player1)

        self.state = GameState.ENDLESS_PLAYING

    def check_round_end(self) -> bool:
        if not self.player1 or not self.player2:
            return False

        p1_dead = self.player1.health <= 0
        p2_dead = self.player2.health <= 0
        time_up = self.round_timer <= 0

        if p1_dead or p2_dead or time_up:
            if p1_dead and not p2_dead:
                winner = 2
            elif p2_dead and not p1_dead:
                winner = 1
            else:
                if self.player1.health > self.player2.health:
                    winner = 1
                elif self.player2.health > self.player1.health:
                    winner = 2
                else:
                    winner = 0

            if winner == 1:
                self.p1_wins += 1
                self.round_transition_text = "PLAYER 1 WINS!"
            elif winner == 2:
                self.p2_wins += 1
                if self.game_mode == "pvc":
                    self.round_transition_text = "CPU WINS!"
                else:
                    self.round_transition_text = "PLAYER 2 WINS!"
            else:
                self.round_transition_text = "DRAW!"

            self.round_transition = True
            self.round_transition_timer = 180
            self.state = GameState.ROUND_END
            return True

        return False

    def check_game_over(self) -> bool:
        if self.p1_wins >= 2:
            self.state = GameState.GAME_OVER
            return True
        elif self.p2_wins >= 2:
            self.state = GameState.GAME_OVER
            return True
        return False

    def handle_player_input(self, keys):
        if not self.player1 or not self.player2:
            return

        p1_move_input = 0
        p2_move_input = 0

        self.player1.is_blocking = False
        self.player2.is_blocking = False

        if self.player1.hitstun <= 0 and self.player1.grounded_timer <= 0:
            if self.player1.dodge_timer <= 0:
                if not self.player1.is_attacking:
                    if not self.player1.is_ultimate:
                        if keys[pygame.K_a]:
                            p1_move_input = -1
                        if keys[pygame.K_d]:
                            p1_move_input = 1

                        if keys[pygame.K_w] and self.player1.jump_count < self.player1.max_jumps:
                            self.player1.jump()

                        if keys[pygame.K_s]:
                            self.player1.state = CharacterState.CROUCH
                            self.player1.block_high = False

                        if keys[pygame.K_j]:
                            self.player1.start_attack(get_light_attack())
                        if keys[pygame.K_k]:
                            self.player1.start_attack(get_heavy_attack())

                        if keys[pygame.K_l]:
                            if self.player1.is_grounded:
                                self.player1.is_blocking = True
                                self.player1.state = CharacterState.BLOCK
                                if keys[pygame.K_s]:
                                    self.player1.block_high = False
                                else:
                                    self.player1.block_high = True

                        if keys[pygame.K_SPACE] and self.player1.rage >= self.player1.max_rage:
                            self.player1.start_ultimate()

                        if keys[pygame.K_LSHIFT] and self.player1.dodge_cooldown <= 0:
                            dodge_dir = -self.player1.facing if p1_move_input == 0 else p1_move_input
                            self.player1.start_dodge(dodge_dir)

        if self.game_mode == "pvp":
            if self.player2.hitstun <= 0 and self.player2.grounded_timer <= 0:
                if self.player2.dodge_timer <= 0:
                    if not self.player2.is_attacking:
                        if not self.player2.is_ultimate:
                            if keys[pygame.K_LEFT]:
                                p2_move_input = -1
                            if keys[pygame.K_RIGHT]:
                                p2_move_input = 1

                            if keys[pygame.K_UP] and self.player2.jump_count < self.player2.max_jumps:
                                self.player2.jump()

                            if keys[pygame.K_DOWN]:
                                self.player2.state = CharacterState.CROUCH
                                self.player2.block_high = False

                            if keys[pygame.K_KP1] or keys[pygame.K_1]:
                                self.player2.start_attack(get_light_attack())
                            if keys[pygame.K_KP2] or keys[pygame.K_2]:
                                self.player2.start_attack(get_heavy_attack())

                            if keys[pygame.K_KP3] or keys[pygame.K_3]:
                                if self.player2.is_grounded:
                                    self.player2.is_blocking = True
                                    self.player2.state = CharacterState.BLOCK
                                    if keys[pygame.K_DOWN]:
                                        self.player2.block_high = False
                                    else:
                                        self.player2.block_high = True

                            if keys[pygame.K_RETURN] and self.player2.rage >= self.player2.max_rage:
                                self.player2.start_ultimate()

                            if keys[pygame.K_RSHIFT] and self.player2.dodge_cooldown <= 0:
                                dodge_dir = -self.player2.facing if p2_move_input == 0 else p2_move_input
                                self.player2.start_dodge(dodge_dir)

        if not self.player1.is_blocking and not self.player1.is_attacking:
            if self.player1.hitstun <= 0 and self.player1.dodge_timer <= 0:
                if p1_move_input != 0:
                    from config import WALK_SPEED
                    self.player1.vel_x = p1_move_input * WALK_SPEED
                    if self.player1.state != CharacterState.JUMP and self.player1.is_grounded:
                        self.player1.state = CharacterState.WALK
                else:
                    if self.player1.is_grounded and self.player1.state == CharacterState.WALK:
                        self.player1.state = CharacterState.IDLE

        if self.game_mode == "pvp":
            if not self.player2.is_blocking and not self.player2.is_attacking:
                if self.player2.hitstun <= 0 and self.player2.dodge_timer <= 0:
                    if p2_move_input != 0:
                        from config import WALK_SPEED
                        self.player2.vel_x = p2_move_input * WALK_SPEED
                        if self.player2.state != CharacterState.JUMP and self.player2.is_grounded:
                            self.player2.state = CharacterState.WALK
                    else:
                        if self.player2.is_grounded and self.player2.state == CharacterState.WALK:
                            self.player2.state = CharacterState.IDLE

    def handle_events(self):
        events = pygame.event.get()
        keys = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False

        if self.state == GameState.MENU:
            self.main_menu.update()
            selection = self.main_menu.handle_input(keys, events)

            if selection is not None:
                if self.main_menu.menu_type == "main":
                    if selection == 0:
                        self._pending_mode = "normal"
                        self.main_menu.set_menu("mode")
                    elif selection == 1:
                        self._pending_mode = "endless"
                        self.hero_select_menu.reset_selection()
                        self.hero_select_menu.single_player_mode = True
                        self.hero_select_menu.selecting_player = 1
                        self.state = GameState.HERO_SELECT
                    elif selection == 2:
                        self.running = False

                elif self.main_menu.menu_type == "mode":
                    if selection == 0:
                        self.game_mode = "pvp"
                        self.start_game()
                    elif selection == 1:
                        self.game_mode = "pvc"
                        self.main_menu.set_menu("difficulty")
                    elif selection == 2:
                        self.main_menu.set_menu("main")

                elif self.main_menu.menu_type == "difficulty":
                    if selection == 0:
                        self.difficulty = "easy"
                        self.start_game()
                    elif selection == 1:
                        self.difficulty = "hard"
                        self.start_game()
                    elif selection == 2:
                        self.main_menu.set_menu("mode")

        elif self.state == GameState.HERO_SELECT:
            self.hero_select_menu.update()
            selection = self.hero_select_menu.handle_input(keys, events)

            if selection is not None:
                result_code, p1_hero, p2_hero = selection
                if result_code == 0:
                    if p1_hero:
                        self.player1_hero_type = p1_hero
                    if p2_hero:
                        self.player2_hero_type = p2_hero

                    if self._pending_mode == "endless":
                        self.start_endless_mode()
                    else:
                        if self.game_mode == "pvc":
                            self.player2_hero_type = HeroType.BASIC_FIGHTER
                            self.start_game_after_hero_select()
                        else:
                            self.start_game_after_hero_select()
                elif result_code == 1:
                    if self._pending_mode == "endless":
                        self.main_menu.set_menu("main")
                    else:
                        if self.game_mode == "pvc":
                            self.main_menu.set_menu("difficulty")
                        else:
                            self.main_menu.set_menu("mode")
                    self.state = GameState.MENU

        elif self.state == GameState.ENDLESS_PLAYING:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.ENDLESS_PAUSED
                        self.ingame_menu.selected_index = 0

            if self.player1:
                enemies = self.endless_manager.get_active_enemies() if self.endless_manager else []
                if enemies:
                    self.player1.handle_input(keys, enemies[0])
                else:
                    self.player1.handle_input(keys, self.player1)

        elif self.state == GameState.ENDLESS_PAUSED:
            selection = self.ingame_menu.handle_input(keys, events)

            if selection is not None:
                if selection == 0:
                    self.state = GameState.ENDLESS_PLAYING
                elif selection == 1:
                    self.start_endless_mode()
                elif selection == 2:
                    self.state = GameState.MENU
                    self.main_menu.set_menu("main")
                    self.endless_manager = None

        elif self.state == GameState.ENDLESS_GAME_OVER:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.state = GameState.MENU
                        self.main_menu.set_menu("main")
                        self.endless_manager = None

        elif self.state == GameState.ENDLESS_WAVE_TRANSITION:
            pass

        elif self.state == GameState.PLAYING:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                        self.ingame_menu.selected_index = 0

            if self.player1 and self.player2:
                self.player1.handle_input(keys, self.player2)
                self.player2.handle_input(keys, self.player1)

            if self.ai_controller and self.player1:
                self.ai_controller.update(self.player1)

        elif self.state == GameState.PAUSED:
            selection = self.ingame_menu.handle_input(keys, events)

            if selection is not None:
                if selection == 0:
                    self.state = GameState.PLAYING
                elif selection == 1:
                    self.start_game()
                elif selection == 2:
                    self.state = GameState.MENU
                    self.main_menu.set_menu("main")

        elif self.state == GameState.GAME_OVER:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.state = GameState.MENU
                        self.main_menu.set_menu("main")

    def update(self):
        if self.state == GameState.PLAYING:
            self.round_timer_frames += 1
            if self.round_timer_frames >= FPS:
                self.round_timer_frames = 0
                if self.round_timer > 0:
                    self.round_timer -= 1

            if self.round_transition:
                self.round_transition_timer -= 1
                if self.round_transition_timer <= 0:
                    self.round_transition = False
            else:
                if self.player1 and self.player2:
                    self.player1.update(self.player2)
                    self.player2.update(self.player1)

                    self.player1.check_attack_hit(
                        self.player2,
                        self.effect_manager.effects,
                        self.screen_shake
                    )
                    self.player2.check_attack_hit(
                        self.player1,
                        self.effect_manager.effects,
                        self.screen_shake
                    )

                self.effect_manager.update()

                self.screen_shake.update()

                self.stage.update()

                if not self.check_round_end():
                    pass

        elif self.state == GameState.ROUND_END:
            self.round_transition_timer -= 1
            if self.round_transition_timer <= 0:
                if not self.check_game_over():
                    self.current_round += 1
                    self.start_new_round()
                    self.state = GameState.PLAYING

        elif self.state == GameState.MENU:
            self.main_menu.update()
            self.stage.update()

        elif self.state == GameState.HERO_SELECT:
            self.hero_select_menu.update()
            self.stage.update()

        elif self.state == GameState.ENDLESS_PLAYING:
            if self.endless_manager and self.player1:
                result = self.endless_manager.update(self.player1)

                if result == "game_over":
                    self.state = GameState.ENDLESS_GAME_OVER
                elif result == "transition":
                    self.state = GameState.ENDLESS_WAVE_TRANSITION
                elif result == "wave_complete":
                    pass

                if self.endless_manager.is_transitioning:
                    self.state = GameState.ENDLESS_WAVE_TRANSITION

                enemies = self.endless_manager.get_all_enemies()

                if not self.endless_manager.is_transitioning:
                    self.player1.update(enemies[0] if enemies else self.player1)

                    for enemy in enemies:
                        if enemy.health > 0:
                            other_targets = [e for e in enemies if e != enemy and e.health > 0]
                            all_targets = [self.player1] + other_targets if self.player1 else other_targets
                            if all_targets:
                                nearest = all_targets[0]
                                min_dist = float('inf')
                                for t in all_targets:
                                    dist = abs(t.x - enemy.x)
                                    if dist < min_dist:
                                        min_dist = dist
                                        nearest = t
                                enemy.update(nearest)

                    if self.player1:
                        for enemy in enemies:
                            if enemy.health > 0:
                                self.player1.check_attack_hit(
                                    enemy,
                                    self.effect_manager.effects,
                                    self.screen_shake
                                )

                    for enemy in enemies:
                        if enemy.health > 0:
                            if self.player1 and self.player1.health > 0:
                                enemy.check_attack_hit(
                                    self.player1,
                                    self.effect_manager.effects,
                                    self.screen_shake
                                )

                            for other in enemies:
                                if other != enemy and other.health > 0:
                                    enemy.check_attack_hit(
                                        other,
                                        self.effect_manager.effects,
                                        self.screen_shake
                                    )

                self.effect_manager.update()
                self.screen_shake.update()
                self.stage.update()

        elif self.state == GameState.ENDLESS_WAVE_TRANSITION:
            if self.endless_manager:
                self.endless_manager.transition_timer -= 1
                if self.endless_manager.transition_timer <= 0:
                    self.endless_manager.is_transitioning = False
                    self.state = GameState.ENDLESS_PLAYING

            self.effect_manager.update()
            self.screen_shake.update()
            self.stage.update()

    def render(self):
        self.screen.fill(BLACK)

        shake_x, shake_y = self.screen_shake.get_offset()

        if self.state == GameState.MENU:
            self.stage.render(self.screen)
            self.main_menu.render(self.screen)

        elif self.state == GameState.HERO_SELECT:
            self.stage.render(self.screen)
            self.hero_select_menu.render(self.screen)

        elif self.state in [GameState.PLAYING, GameState.PAUSED, GameState.ROUND_END]:
            self.stage.render(self.screen, shake_x, shake_y)

            if self.player1 and self.player2:
                self.player1.render(self.screen, shake_x, shake_y)
                self.player2.render(self.screen, shake_x, shake_y)

            self.effect_manager.render(self.screen, shake_x, shake_y)

            if self.player1 and self.player2:
                self.ui.render_health_bar(
                    self.screen, 50, 30, 280, 30,
                    self.player1.health, self.player1.max_health,
                    True, self.player1.rage, self.player1.max_rage,
                    "PLAYER 1"
                )

                p2_name = "PLAYER 2" if self.game_mode == "pvp" else "CPU"
                self.ui.render_health_bar(
                    self.screen, SCREEN_WIDTH - 330, 30, 280, 30,
                    self.player2.health, self.player2.max_health,
                    False, self.player2.rage, self.player2.max_rage,
                    p2_name
                )

                self.ui.render_timer(self.screen, self.round_timer)

                self.ui.render_round_score(self.screen, self.p1_wins, self.p2_wins)

                self.ui.render_combo(self.screen, self.player1, self.player2)

            if self.round_transition:
                alpha = 0
                if self.round_transition_timer > 100:
                    alpha = int((120 - self.round_transition_timer) / 20 * 255)
                elif self.round_transition_timer > 30:
                    alpha = 255
                else:
                    alpha = int(self.round_transition_timer / 30 * 255)

                self.ui.render_round_transition(
                    self.screen,
                    self.round_transition_text,
                    alpha
                )

        if self.state == GameState.PAUSED:
            self.ingame_menu.render_pause(self.screen)

        if self.state == GameState.GAME_OVER and self.player1 and self.player2:
            winner_is_p1 = self.p1_wins >= 2

            if winner_is_p1:
                winner_name = "PLAYER 1"
            else:
                winner_name = "CPU" if self.game_mode == "pvc" else "PLAYER 2"

            self.ingame_menu.render_game_over(
                self.screen,
                winner_name,
                self.player1.max_combo,
                self.player2.max_combo,
                self.player1.total_damage_dealt,
                self.player2.total_damage_dealt,
                winner_is_p1
            )

        elif self.state in [GameState.ENDLESS_PLAYING, GameState.ENDLESS_WAVE_TRANSITION, GameState.ENDLESS_PAUSED]:
            self.stage.render(self.screen, shake_x, shake_y)

            if self.player1:
                self.player1.render(self.screen, shake_x, shake_y)

            if self.endless_manager:
                enemies = self.endless_manager.get_all_enemies()
                for enemy in enemies:
                    if enemy.health > 0:
                        enemy.render(self.screen, shake_x, shake_y)

            self.effect_manager.render(self.screen, shake_x, shake_y)

            if self.player1:
                self.ui.render_health_bar(
                    self.screen, 50, 30, 280, 30,
                    self.player1.health, self.player1.max_health,
                    True, self.player1.rage, self.player1.max_rage,
                    "PLAYER 1"
                )

            if self.endless_manager:
                diff_color = self.endless_manager.difficulty.get_color_for_difficulty()
                diff_desc = self.endless_manager.difficulty.get_difficulty_description()

                self.ui.render_endless_hud(
                    self.screen,
                    self.endless_manager.stats.current_wave,
                    self.endless_manager.get_survival_time_formatted(),
                    self.endless_manager.stats.current_combo_kills,
                    self.endless_manager.stats.score,
                    diff_color,
                    diff_desc
                )

            if self.endless_manager and self.endless_manager.is_transitioning:
                alpha = 0
                timer = self.endless_manager.transition_timer
                if timer > ENDLESS_WAVE_TRANSITION_FRAMES - 20:
                    alpha = int((ENDLESS_WAVE_TRANSITION_FRAMES - timer) / 20 * 255)
                elif timer > 30:
                    alpha = 255
                else:
                    alpha = int(timer / 30 * 255)

                current_wave = self.endless_manager.stats.current_wave
                self.ui.render_endless_wave_transition(
                    self.screen,
                    current_wave,
                    alpha,
                    ENDLESS_WAVE_HEAL_AMOUNT if current_wave > 1 else 0
                )

        if self.state == GameState.ENDLESS_PAUSED:
            self.ingame_menu.render_pause(self.screen)

        if self.state == GameState.ENDLESS_GAME_OVER and self.endless_manager:
            stats = self.endless_manager.stats
            self.ingame_menu.render_endless_game_over(
                self.screen,
                stats.current_wave,
                self.endless_manager.get_survival_time_formatted(),
                stats.total_kills,
                stats.max_combo,
                stats.score,
                stats.gold_reward,
                stats.exp_reward,
                stats.talent_points_reward
            )

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
