# Python Maze Adventure — The Coin Mission

**Year 6 Digital Technologies · 90 minutes · Australian English · absolute beginners**

| | |
|---|---|
| **Year level** | 6 (students aged 11–12) |
| **Duration** | 90 minutes (single lesson) |
| **Curriculum** | Australian Curriculum v9 Digital Technologies — **AC9TDI6P02**: *Design algorithms involving multiple alternatives (branching) and iteration* |
| **General capabilities** | Critical and creative thinking; Numeracy (number, pattern); Literacy (technical vocabulary); Personal and social capability |
| **Prior learning** | Variables and `print()` were met in the previous lesson. No other coding experience is assumed. |
| **Main resources** | The game (`game/main.py`), the 24-slide deck (`slides/index.html`) and this plan |
| **Teacher-only answer key** | `answers/answer_key.html` — Create code, four maze routes and Boss code. Do not project or share. |
| **Working with** | Individual machines during game play; pairs for predict–check–explain activities |

---

## 1. Lesson at a glance

| Time | Section | Slides | What students do |
|---|---|---|---|
| 0–5 | Hook and goals | 1–2 | Meet the story; see that Python ideas come first and the game is practice |
| 5–15 | Review | 3–6 | Variables, comparison operators, `if`/`else`; three-question quiz |
| 15–27 | Input and `int()` | 7–10 | Learn `input()` and `int()`, see a worked example, take the quiz, then write the Create program from an empty editor |
| 27–45 | `for` loops | 11–15 | See the copy-paste problem, learn `range()`, trace a loop, run a game loop, take the quiz |
| 45–58 | Functions | 16–20 | Define and call a function, add a parameter, build `move_right(steps)`, take the quiz |
| 58–63 | Meet the game | 21–22 | Tour the UI, command strip, Hint button and the four-level rules |
| 63–78 | Maze play | — | Solve four levels from easy to hard; use hints, not answers |
| 78–87 | Boss | — | Write `super_attack()` with `if coins >= 30` and defeat the boss |
| 87–90 | Review and exit ticket | 23–24 | Summarise the four ideas; complete the exit ticket |

> **Timing discipline:** the knowledge sections are the lesson, and the maze is where students practise it. Protect slides 3–20. If time runs short, shorten the whole-class discussion after a quiz rather than cutting the guided examples.

---

## 2. Whole-lesson learning intention and success criteria

**Learning intention**
> We are learning four Python ideas — decisions, input, loops and functions — and using them to guide a robot through a maze and defeat a boss.

**Success criteria** — *By the end of the lesson I can:*
1. Use `input()` to ask the player for a name, store it in a variable and print it.
2. Use a `for` loop with `range()` to repeat an action a set number of times.
3. Define and call a function with a parameter, such as `move_right(steps)`.
4. Use `if` and `else` to attack only when `coins >= 30`.

Display these four criteria at the start and tick them off on the board as the lesson progresses. The deck returns to them on slide 23.

---

## 3. Before the lesson — teacher setup (10 minutes, not part of the lesson)

1. **Launch the game**: double-click `run_game.command` (macOS), `run_game.bat` (Windows), or run `python game/main.py`. The window opens at 1280 × 800 and is resizable.
2. **Check the projector.** The arena is on the left and the editor on the right. Use **F11** or the window button if needed.
3. **Check sound.** The **Sound** button in the header toggles between **Sound** and **Muted**. Use **Muted** for a quiet class.
4. **Open the slides** by double-clicking `slides/index.html`. Press **F** for full screen. Arrow keys, Space and Page Up/Page Down move through the 24 slides; **Home** and **End** jump; **N** shows presenter notes; **B** blacks out the screen; **R** resets the quizzes; **?** lists the keys.
5. **Keep the answer key closed.** `answers/answer_key.html` is for the teacher only. If you need to check a route, open it on the teacher laptop, not the projector.
6. **Test one quiz** on slides 6, 10, 15 or 20 before class: a wrong answer says "Not quite — try again"; a correct answer turns green and reveals the explanation.
7. **Pair students** and remind them: "You may talk through the plan together, but every person types some of the code."

**Keyboard reference for the game**

| Action | Keys |
|---|---|
| Run code | **Ctrl + Enter** (or **Cmd + Enter**) |
| Stop code | **Ctrl + Enter** again, **Esc**, or the **Stop** button |
| Help and all commands | **F1** |
| Reset the current level or stage | the **Reset** button |
| Speed | 1× → 2× → Instant button |
| Hints | the **Hint** button beside the mission title |
| Preview a level | click the level dots 1–4 on the Maze stage |

---

## 4. Hook and goals

**Slides 1–2**

0–5 minutes

### Learning intention
> We are learning the Python ideas first, then using the game to practise them.

### Teacher script
> "Today the game is not the lesson — it is the practice ground. We will learn four ideas: decisions, asking for input, loops, and functions. Every command in the maze is one of those ideas wearing a robot costume."

Read the four learning goals on slide 2. Point out the deliberate order: review, input, loops, functions, and only then the game. State that the editors start empty: students will write every line themselves, with a command strip and hints available.

### Activity (3 minutes)
- Ask: "What is the difference between knowing a recipe and cooking a meal?" Use the answer to introduce the gap between reading code and writing it.
- Show the three stage names: **Create Your Explorer**, **Escape the Maze**, **Super Attack**. Explain that the first is a short program, the second is four levels, and the third is the boss.

### Expected outcomes
Students know the four goals, the three stages and the rule that the game comes last. No devices needed yet.

---

## 5. Review

**Slides 3–6**

5–15 minutes

### Learning intention
> We are remembering how variables, comparison operators and `if`/`else` work, because the maze and the boss both use them.

### Teacher script and worked examples
- **Slide 3 — variables.** Show `coins = 50`, then `coins = coins - 1`, then `print(coins)` → `49`. Read the assignment right to left: take the current value, subtract one, put it back.
- **Slide 4 — comparison operators.** Show that `==`, `>`, `<` and `>=` all answer `True` or `False`. The boss uses `coins >= 30`, and exactly 30 passes. Stress `=` (put a value in a box) versus `==` (ask a question).
- **Slide 5 — if-else.** Trace the snippet with 34 and then 20. Only one branch runs. Point to the colon and the indentation.
- **Slide 6 — Review Quiz.** Three questions. Students answer independently, then compare with a partner before the class reveals the rule.

### Questions and expected answers
- *"What does `coins = coins - 1` mean?"* — Calculate the right side first, then store the result back in `coins`.
- *"With 30 coins, is `coins >= 30` True or False?"* — True; "at least" includes exactly 30.
- *"If the condition is False, which lines run?"* — The indented lines under `else`.

### Common mistakes
| Mistake | What students see | Fix |
|---|---|---|
| `coins == coins - 1` | Nothing changes; this is a question, not an assignment | Use one `=` to store a value |
| `coins = 30` used in an `if` | The condition is always true and overwrites the count | Use `==` or `>=` in the question |
| Missing colon after `if` | Syntax error | Add `:` at the end of the condition line |
| Missing indent under `if` | `IndentationError` or the branch does not run | Indent the body four spaces |

### Expected outcomes
Students can predict the output of a short variable program and choose the correct comparison for "at least 30". The quiz answers are on the slide, and the teacher notes give the rules, not just letters.

---

## 6. Input and the Create mission

**Slides 7–10**

15–27 minutes

### Learning intention
> We are learning to ask the player for information with `input()` and turn number text into a real number with `int()`.

### Teacher script and worked examples
- **Slide 7 — `input()`.** The prompt is the text in brackets; the player's answer comes back as text and is stored in a variable. Run a short example live if the projector allows.
- **Slide 8 — `int()`.** `input()` returns text even for digits. `int("7")` is the number 7. `int("seven")` raises an error. Show the nested form `int(input("How many steps? "))`. This is a general skill: the game fixes `weapon_power` at 5, so the Create mission asks no numbers.
- **Slide 9 — Putting Input Together.** Walk through the single question, the `player_name` variable, and the welcome `print()`. Point out that the answer is already text, so no conversion is needed. This is the worked example for the Create mission.
- **Slide 10 — Input Quiz.** Three questions: return type, conversion, and correct nesting.

### Create mission — students write their own code (6–7 minutes)
1. Open the game and the **Create Your Explorer** stage. The editor is empty.
2. Students write their own program using the command strip: ask for `player_name` with `input()`, then print a welcome that includes the name.
3. Run with **Ctrl + Enter**. Answer the one dialog. The robot's name appears above it, and the success card confirms that weapon power is fixed at 5.
4. The game checks the work: a blank program, a name typed straight into the code instead of `input()`, or a missing `print()` all keep the mission open and show a friendly correction.
5. If a student is stuck, direct them to the **Hint** button. Hints are progressive: first the idea, then the structure, then the key command. They never contain the full program.
6. Students who finish early should add a second `print()` line or change the welcome wording, then rerun to check the output.

### Questions and expected answers
- *"Why does this program not need `int()`?"* — The only answer is a name, and `input()` already returns text. `int()` is for number text, which the next example uses.
- *"What is `player_name`?"* — A variable: a labelled box holding a value.
- *"Why does the game not ask for weapon power?"* — The mission fixes `weapon_power` at 5 so students focus on input and output; they may still print it.

### Common mistakes
| Mistake | What students see | Fix |
|---|---|---|
| `input` without brackets | No dialog; a message about the function | Call it: `input("...")` |
| Name typed straight into the code | The game asks the program to use `input()` | Ask with `input()` and store the answer |
| Name never printed | The game asks for a `print()` that includes `player_name` | Print the welcome after asking |
| Quotation marks missing | `NameError` with a tip | Put the question inside quotes |
| Blank editor | The game keeps the mission open and shows "Almost there!" | Write the two lines, then run again |

### Expected outcomes
Every student has written and run a Create program from an empty editor and seen their explorer named. The check is the game's success card, not copied code.

---

## 7. For loops

**Slides 11–15**

27–45 minutes

### Learning intention
> We are learning to repeat instructions with a `for` loop and `range()`, so one short program can take many steps.

### Teacher script — the five-step loop sequence
1. **Slide 11 — the copy-paste problem.** Show four repeated `move_one_step_right()` lines. Ask what forty steps would look like. Repetition works but does not scale.
2. **Slide 12 — the tool.** Write `for i in range(3):` with an indented `move_one_step_right()`. Point out the colon and the indent. `range(5)` means five repeats, counted from 0.
3. **Slide 13 — trace it.** Fill in the trace table together: passes 1, 2, 3 with `i` values 0, 1, 2; coins 29, 28, 27 from a start of 30. The body does not run for `i = 3`.
4. **Slide 14 — the game loop.** Run eight steps in a straight corridor. Change the count to twelve. The print statement outside the loop runs once.
5. **Slide 15 — For Loop Quiz.** Repeat count, colon, and coin cost.

### Activity (8 minutes) — "change one number"
- Students open the **Escape the Maze** stage and click level 1 (the level dots are a teacher/student preview; the intended campaign flow is still sequential).
- Write a loop that crosses the first straight corridor, using the command strip to check the command names.
- Change the count once. Observe the step and coin counters.
- Keep the route simple: this is a loop exercise, not a route-planning exercise yet. The four-level campaign comes after all four ideas have been taught.

> Note: levels 1–4 are not solved in this section. Students should not race ahead; the maze play block begins at 63 minutes, after functions.

### Questions and expected answers
- *"How many times does `range(5)` repeat?"* — Five times.
- *"What does the colon do?"* — It opens the loop body; the indented lines are repeated.
- *"Why does the print line run once?"* — It is not indented, so it is outside the loop.

### Common mistakes
| Mistake | What students see | Fix |
|---|---|---|
| Missing colon | Syntax error on the `for` line | Add `:` |
| Body not indented | The line runs once after the loop, or an error appears | Indent four spaces |
| `range(3)` expected to run four times | One extra or one missing step | `range(n)` is n passes, from 0 to n−1 |
| Changing the loop count but not the route | The robot hits a wall and coins stop dropping | A wall does not charge a coin; fix the route and rerun |

### Expected outcomes
Students can trace a three-pass loop and predict the coin cost. They have run a loop in level 1 and changed its count deliberately.

---

## 8. Functions

**Slides 16–20**

45–58 minutes

### Learning intention
> We are learning to define our own function, give it a parameter, and call it with different values.

### Teacher script and worked examples
- **Slide 16 — the idea.** A function is a named recipe. Define it once, call it whenever needed. Our game functions do something on screen; they do not return a value.
- **Slide 17 — define and call.** Show `def move_right():` with a three-step loop inside, then a call at the bottom. Delete the call to show that defining alone does nothing.
- **Slide 18 — parameters.** Change the definition to `def move_right(steps):` and the loop to `range(steps)`. Call it with 3 and with 8. The parameter is the slot; the argument is the value.
- **Slide 19 — build it.** Two calls, 2 and 8, total ten steps and ten coins. The helper is a tool, not an answer: students still plan the turns and the step counts.
- **Slide 20 — Function Quiz.** `def` versus call, the value of a parameter, and define-before-call.

### Activity (6 minutes) — write the helper from memory
- In the editor, students type the two-line helper `move_right(steps)` and two calls of their choice.
- Run it on level 1 or 2 to confirm the step and coin counters move by the sum of the arguments.
- Ask students to explain the difference between `steps` (the parameter) and `8` (the argument) to a partner.

### Questions and expected answers
- *"What does `def` do?"* — It defines a function and gives it a name; it does not run the body.
- *"What is a parameter?"* — A named slot in the definition that receives a value when the function is called.
- *"Why define before calling?"* — Python needs the definition before the call is executed.

### Common mistakes
| Mistake | What students see | Fix |
|---|---|---|
| Calling before the `def` | Name error: the function is not defined yet | Move the definition above the call |
| Forgetting the brackets in the call | The function is named but not run | Write `move_right(3)`, not `move_right` |
| Forgetting the argument | Error about a missing argument | Supply a number: `move_right(8)` |
| Indenting the call under the definition | The call becomes part of the function and never runs | Put calls at the left margin |

### Expected outcomes
Students can define and call `move_right(steps)` without copying a full route. They can point to the definition, the parameter and a call, and explain each in one sentence.

---

## 9. Meet the game

**Slides 21–22**

58–63 minutes

### Learning intention
> We are learning how the game is organised, so we can practise the four ideas without hunting for commands.

### Teacher script
- **Slide 21 — the interface.** Tour the arena, level dots, Hint button, command strip, empty editor and console. The editor is empty on purpose. The command strip is a reference, not starter code. Show **Ctrl + Enter** and **Stop**.
- **Slide 22 — four levels, one budget.** Read the level table and the economy rules:
  - Every move costs 1 coin, whichever direction it goes.
  - Gold coin +10; treasure chest +20.
  - Reach the base before the coins hit zero.
  - The final base tops the player up to 50 coins for the Boss.
- Explain the difficulty story: level 1 is a five-step corridor; level 2 offers two routes; level 3 has a budget tighter than the shortest route; level 4 is the final level and needs the dead-end chest to pay for the long way.
- Do **not** reveal any route. The answer key stays closed.

### Questions and expected answers
- *"What does the Hint button give?"* — One idea at a time, never the full code. On the last maze hint it may offer to draw the reference route on the map.
- *"What happens if I reach the base with 0 coins?"* — The level passes; failure only happens when coins run out before the base.
- *"Why does the last level top up to 50?"* — So the Boss map can charge 1 coin for each of the 20 steps to the attack pad, and the robot still arrives with 30.

### Expected outcomes
Students can name the four levels, their start coins and the two supply values. They know where the command strip and Hint button are before the campaign begins.

---

## 10. Maze play — 63–78 minutes

### Learning intention
> We are applying loops, functions and route planning to solve four levels with a budget.

### Activity (15 minutes)
1. Students stay on the **Escape the Maze** stage and click level 1. Work through levels in order: **First Steps** (30 coins, five steps), **Two Paths** (35), **Save Your Coins** (22), **The Chest Detour** (33).
2. Use `move_right(steps)` for corridors. Each move command names its own direction. The command strip lists every available method: `move_one_step_up()`, `move_one_step_down()`, `move_one_step_left()`, `move_one_step_right()`, `coins` and `print()`.
3. Read the objective card before moving. Ask: "How many steps does my plan cost? How many coins do I have? Which supplies can I reach without running out?"
4. Use **Hint** when stuck. Work through one hint at a time and rerun the program after each idea.
5. Reach the base to pass. Running out of coins before the base fails the level; **Reset** restarts the current level with its own start coins.
6. The **Next level** button on the success card advances the campaign. The level dots let a teacher preview any level, but the intended flow is sequential.

### Teacher circulation prompts
- *"What is your step count, and what is your coin budget?"*
- *"Which line is the loop, and what is the loop count?"*
- *"Where is the chest, and what does it pay?"*
- *"What happens if you collect the supplies in a different order?"*
- *"Can you shorten the code with your helper without changing the route?"*

### Differentiation
- **Support:** start with level 1 only; write the straight route one step at a time, then replace repeated steps with a loop. Use the first two hints before moving.
- **Core:** complete levels 1–3 with at least one use of `move_right(steps)` per level.
- **Extension:** on level 4, compare the direct route with the chest detour and explain why the direct route runs out of coins. Write a short comment (or a console `print`) that states the step budget before running.

### Expected outcomes
Most students complete levels 1–2; many complete level 3; level 4 is a stretch. The goal is strategic thinking and correct use of the helper, not speed. Every student should be able to say why a route failed, using the word "budget".

### Common mistakes
| Mistake | What students see | Fix |
|---|---|---|
| Planning by eye without counting steps | Coins hit zero before the base | Count steps and supplies before running |
| Adding one move too many | Coins hit zero before the base | Count every `move_one_step_` line against the budget |
| Walking into a wall | A BONK line; coins do not change | Move in a different direction, not the one that faces the wall |
| Walking the level 4 direct route without the chest | Not enough coins for the long way | Collect the chest before the final corridor |
| Calling the helper but forgetting to call it | No movement | Add the call at the left margin |

---

## 11. Boss — 78–87 minutes

### Learning intention
> We are applying `if`/`else` and functions to make one decision: attack only with enough coins.

### Activity (9 minutes)
1. After the final maze success card, choose **Next mission** to enter **Super Attack**. The robot starts at the top-left start tile. A completed campaign starts with the 50-coin checkpoint; a practice run also starts with 50 coins.
2. Checkpoint first: walk to the **cyan attack pad** two tiles above the boss. Every move costs 1 coin, the shortest walk is 20 steps, and the boss tile itself is blocked. The robot arrives with exactly 30 coins.
3. The available functions are listed from the start: the four `move_one_step_` commands, `fire_super_attack()` and `coins`. The editor is empty.
4. Students write `super_attack()`:
   - check `coins >= 30` with an `if` line;
   - call `fire_super_attack()` inside the true branch;
   - print `"Super Attack Activated!"` on success and `"Not enough coins!"` on failure;
   - call `super_attack()` at the bottom.
5. Run and read the console. If the robot is not on the pad, or the fire call is not inside the `coins >= 30` check, the game refuses the attack and says what to fix. If the function is defined but never called, the boss stays standing.
6. Use **Hint** for the pad, then the if/else structure, then the position of `fire_super_attack()`. The hint never provides the whole program.
7. Students who finish early change the condition to a higher number and run again to see the failure path, then restore 30.

### Questions and expected answers
- *"Why does the boss need 30 coins?"* — The super attack costs 30; the `if` checks the budget before firing. The 20-step walk is designed to leave exactly 30.
- *"Why must I stand on the pad?"* — The beam fires from the pad at the boss; away from the pad the game refuses the attack and spends no coins.
- *"What happens if I write `fire_super_attack()` without an `if`?"* — The game refuses it and asks for the `coins >= 30` check.
- *"What happens if the condition is False?"* — The `else` branch runs and the boss remains.
- *"What makes the function run?"* — The call `super_attack()` after the definition.

### Expected outcomes
Students walk to the pad, defeat the boss by writing their own function with a `coins >= 30` guard, and can explain the two branches. No student needs the answer key; the hints and the game notices are sufficient.

---

## 12. Review and exit ticket

**Slides 23–24**

87–90 minutes

### Learning intention
> We are checking that we can explain the four Python ideas, not just play the game.

### Activity (3 minutes)
- Slide 23: use quick hands or whiteboards for the five review questions. Tick the four success criteria together.
- Slide 24: students complete the exit ticket on paper or in their books:
  1. Write a `for` loop that moves five steps.
  2. Write the line that asks for a name and stores it.
  3. In one sentence, why use a function instead of copying code?

### Expected answers
1. `for i in range(5):` followed by an indented `move_one_step_right()`.
2. `player_name = input("What is your name? ")`.
3. A function names a reusable block: write it once, call it many times, and change a parameter instead of copying lines.

### Assessment
| Evidence | What it shows |
|---|---|
| Create program runs | `input()` returns text; the answer is stored in `player_name` and printed in a welcome |
| Level 1–2 completion | A loop crosses a corridor; the coin budget is understood |
| Level 3–4 reasoning | The student plans around a supply and can explain a failed budget |
| `move_right(steps)` in code | Define/call distinction; parameters and arguments |
| Boss success and failure path | `if`/`else`, comparison, function call, debugging from the notice |
| Exit ticket | Transfer of the four ideas to new examples |

Sort exit tickets into **ready** and **revisit**. Revisit students need the loop trace and the define/call distinction before the next lesson.

---

## 13. Differentiation and support

- **Visual anchors:** keep the command strip visible; point to the objective card before each level; use the hint dots to show progress through hints.
- **Language:** say "parameter slot, argument value"; say "budget" for coins; say "route" for the sequence of turns and steps.
- **Pairs:** one plans the route aloud, the other types; swap after each level.
- **Support:** allow a two-line `input()`/`int()` form on slide 8 instead of nesting the calls; the Create mission itself needs only `input()` and `print()`. Allow a step-by-step route before replacing it with a helper.
- **Extension:** ask for a written plan with step count, supply count and final coins before running level 4. Ask students to refactor three repeated moves into a loop or helper.
- **No copying answers:** the editor is empty on purpose. If a student asks for "the code", reply with the next hint or a question about their plan.

## 14. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Students rush to the game and skip the knowledge sections | The game sections are timed after slides 16–20; hide the app until slide 21 |
| Students copy a route instead of planning | Empty editors, hints only, and teacher circulation questions about step counts |
| Level 4 frustration | Permit partner planning and the final route hint; the pass condition only requires reaching the base with 0 or more coins |
| Boss confusion about coins | The final level tops the checkpoint up to 50; practice runs start with 50; every move costs 1 and the 20-step walk leaves exactly 30 |
| Answer key leaked to students | Keep `answers/answer_key.html` closed; it is marked "Teacher answer key — do not project" |
| Sound distracting | Use the **Muted** setting before the lesson |
| Time overrun | Shorten the quiz discussion, never the maze play or the Create typing time |
