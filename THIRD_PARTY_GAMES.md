# Third-party mini-games

The Android pilot bundles the following upstream projects as pinned git submodules. Each project is distributed under the MIT License; its upstream LICENSE file is retained inside the corresponding submodule and is packaged with the application assets.

- 2048 — gabrielecirulli/2048 — commit 478b6ec346e3787f589e4af751378d06ded4cbbc
- Tower Game — iamkun/tower_game — commit c6fa84afe179b661fa71cf7cc8788d0c47ca2875
- Suika Game — sergiss/suika_game — commit ac0398e12001039320cbae2c977ab091fc571044
- Match-3 Game HTML5 — rembound/Match-3-Game-HTML5 — commit be7df47403668623ed40073fa87d39d9b4c7da2d
- Bubble Shooter HTML5 — rembound/Bubble-Shooter-HTML5 — commit 2e62806ef5d7471f77566bc1cf6f2ac17a584c4d
- Cozy Café · Memories 2010 — nisanurtezcan/cozyCafeGame — commit 24d7f7be4913fe6a532bb13655e05430f86e4767

The host application keeps the upstream repositories pinned and unmodified. A local Android adaptation layer adds a secure appassets origin, mobile viewport/layout patches, touch semantics, the 60-second session lifecycle, and learning-session integration. Upstream license files remain packaged with each game.


## Production adaptations

The Rembound Match-3 submodule remains pinned for source history and its MIT notice, but the production Match 3 adapter now points to an original offline `game_custom/match3` implementation with power gems and mobile-first interaction. Other upstream game repositories remain pinned and unmodified; their mobile presentation changes are applied by the Android host adaptation layer.
