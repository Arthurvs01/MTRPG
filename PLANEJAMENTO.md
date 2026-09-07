# PLANEJAMENTO MTRPG - Mushoku Tensei RPG Bot

---

## INSTRUÇÕES PARA A IA

1. **Executar tarefas descritas neste arquivo** - Ler e seguir as tarefas listadas abaixo
2. **Marcar como concluído após executar** - Atualizar `[ ]` para `[X][dd/mm/aaaa - hh:mm:ss]` imediatamente após completar cada tarefa
3. **Adicionar tarefas novas antes de fazer** - Inserir novas tarefas no arquivo ANTES de começar a implementar para evitar perda em interrupções
4. **Sempre testar o que for implementado** - Rodar testes unitários (`python -m pytest tests/ -v`) e validar imports (`python3 -c "from main import build_app"`)
5. **Validar que botões chamam menus existentes** - Verificar se `callback_data` dos botões têm handlers registrados no `main.py`
6. **Manter consistência** - Seguir padrões existentes de código, nomenclatura e arquitetura
7. **Documentar mudanças** - Atualizar este arquivo com o que foi feito
8. **Resolver Problemas** - Sempre resolver aquiloque estiver listado em "PROBLEMAS"

---

## DESCRIÇÃO DETALHADA DO PROJETO

### Arquitetura de Pastas e Arquivos

```
MTRPG/
├── main.py                    # Entry point, registra handlers, constroi Application
├── config.py                  # Configurações globais, carrega .env, paths, constantes
├── .env                       # Variáveis de ambiente (BOT_TOKEN, DATABASE_DIR)
├── PLANEJAMENTO.md           # Este arquivo
├── content/
│   ├── data/                 # JSONs de dados estáticos do jogo
│   │   ├── classes_races.json    # Raças e Vocações com bônus
│   │   ├── items.json            # Itens, equipamentos, lojas
│   │   ├── monsters.json         # Bestiário completo
│   │   ├── quests.json           # 40 missões (20 Fittoa + 20 Rikarisu)
│   │   ├── regions.json          # 8 regiões progressivas
│   │   ├── spells.json           # 7 feitiços canônicos
│   │   ├── crafting_recipes.json # 8 receitas de forja
│   │   ├── lootboxes.json        # 4 tipos de baús
│   │   └── sword_skills.json     # 6 técnicas de espada
│   ├── texts/                # Templates de mensagens (.txt com placeholders)
│   │   ├── *.txt (26 arquivos)
│   └── images/               # Imagens para menus (referenciadas por nome)
├── core/
│   ├── json_loader.py        # Carregador centralizado com cache para JSONs
│   ├── text_loader.py        # Carregador de templates de texto com formatação
│   ├── message_manager.py    # Envio/edição de mensagens com imagens
│   └── callback_router.py    # Roteador de callbacks de texto (estados de conversa)
├── database/
│   ├── player_repo.py        # Persistência assíncrona de players (JSON atômico)
│   ├── quest_repo.py         # Repositório de missões (filtro por rank/região, board diário)
│   ├── item_repo.py          # Catálogo de itens/equipamentos
│   └── market_repo.py        # Mercado player-to-player (cache em memória + persistência)
├── models/
│   ├── player.py             # Entidade Player completa (atributos, inventário, skills, etc.)
│   ├── item.py               # Item, Equipment (raridade, upgrade +1 a +10, runas)
│   ├── quest.py              # Quest dataclass
│   └── skill.py              # Spell, SwordSkill dataclasses
├── systems/
│   ├── login_system.py       # Registro: nome -> raça -> vocação -> cria player
│   ├── progression_system.py # XP, level up, status points, guild ranks, touki awakening
│   ├── combat_system.py      # Turn-based combat com estilos de espada, magia, touki, demon eye
│   ├── magic_system.py       # Feitiços por elemento/rank, conjuração silenciosa
│   ├── sword_system.py       # Técnicas dos 3 estilos de espada
│   ├── energy_system.py      # Energia de ação, descanso na estalagem (3 modos)
│   ├── training_system.py    # 3 treinos/dia (espada, magia, touki) -> apenas XP
│   ├── quest_system.py       # Aceitar/completar/resgatar missões (limite 2/dia, 1 ativa)
│   ├── crafting_system.py    # Forja com raridade aleatória, upgrade nível, engaste runas
│   ├── lootbox_system.py     # 4 baús (diário grátis, caça, diamantes)
│   ├── dungeon_system.py     # Dungeons em grupo (2-4 players, 5 waves, boss, recompensas por dano)
│   ├── party_system.py       # Grupos de aventureiros (até 10, líder, fundos, convites)
│   └── inventory_system.py   # Consumíveis, equipar, comprar da loja NPC
├── world/                    # Menus/Handlers de UI (CallbackQueryHandlers)
│   ├── hub_menu.py           # Menu principal
│   ├── guild_menu.py         # Guilda: missões ativas, quadro, aceitar/resgatar
│   ├── exploration_menu.py   # Caçada na região atual
│   ├── travel_menu.py        # Mapa mundi, viagens entre regiões
│   ├── inn_menu.py           # Estalagem: 3 tipos de descanso
│   ├── training_menu.py      # Dojo/Torre/Condicionamento
│   ├── crafting_menu.py      # Forja por categoria, upgrades, runas
│   ├── market_menu.py        # Mercado P2P com filtros
│   ├── dungeon_menu.py       # Criar/entrar/iniciar dungeon, combate por ondas
│   ├── party_menu.py         # Grupo: criar, convidar, fundos, transferir liderança
│   ├── lootbox_menu.py       # Abrir baús
│   └── character/
│       ├── character_menu.py # Perfil, skills, distribuição de stats
│       └── inventory_menu.py # Mochila, equipamentos, usar/equipar
└── tests/
    └── test_quests_and_menus.py  # 8 testes unitários
```

### Funcionamento do Mundo (Contexto de Jogo)

**Progressão Geográfica (8 Regiões):**
1. **Aldeia Buena (Fittoa)** - Inicial, Lvl 1-5, Rank F, Continente Central
2. **Cidade de Roitree** - Lvl 10+, Rank E, requer Buena
3. **Reino de Asura (Capital)** - Lvl 20+, Rank D, requer Roitree
4. **Continente Milis (Capital Santa)** - Lvl 35+, Rank C, requer Asura
5. **Cidade de Sharia (Grande Floresta)** - Lvl 45+, Rank B, requer Milis
6. **Continente Begaritt (Labirinto)** - Lvl 60+, Rank A, requer Sharia
7. **Cidade de Rikarisu (Continente Demônio)** - Lvl 75+, Rank S, requer Begaritt
8. **Porto do Vento (Costa Norte)** - Lvl 90+, Rank S, requer Rikarisu

**Sistemas Principais:**
- **Registro**: Nome -> Raça (6 opções) -> Vocação (3: Espadachim/Mago/Híbrido) -> Bônus raciais/vocacionais
- **Combate**: Turn-based, iniciativa por velocidade. Espadachim usa estilos de espada + touki. Mago usa feitiços elementais (5 escolas) + conjuração silenciosa. Híbrido mistura ambos.
- **Estilos de Espada**: Deus da Espada (critico/velocidade), Deus da Água (parry/contra-ataque), Deus do Norte (fintas/arremesso)
- **Magia**: 5 escolas (Fogo, Água, Terra, Vento, Cura), 7 ranks (Iniciante a Divino)
- **Touki**: Desperta no nível 3 para Espadachim/Híbrido (revestimento de mana que absorve dano e aumenta stats)
- **Olho Demoníaco**: Premonição (esquiva 40%) ou Clarividência
- **Energia**: 100 max, regen passiva 1/3min. Caça custa 15, Treino custa 20. Estalagem recupera (Simples 20F/+50, Luxo 50F/100%, Diamantes 10D/100%)
- **Missões**: Quadro diário com 4 missões por região. Limite: 1 ativa, 2 conclusões/dia. Tipos: slay (abate)
- **Dungeons**: Grupo 2-4, líder cria com senha 4 dígitos. 5 ondas (4 mobs + boss). Recompensas proporcionais ao dano. Apenas sobreviventes ganham. Parte dos caídos divide entre vivos.
- **Grupos (Party)**: Até 10 membros. Líder convida por Chat ID. Fundos comuns. Transferência de liderança.
- **Forja**: 8 receitas. Raridade aleatória (Comum 55%/1 slot, Raro 30%/2, Santo 11%/3, Imperial 3.5%/4, Divino 0.5%/5). Upgrade +1 a +10 (custo nivel*40F, +12% stats/nível). Runas engastam e escalam com nível do equipamento (+15%/nível).
- **Mercado P2P**: Player anuncia itens da bolsa, outros compram. Filtros por tipo. Ordenado por preço.
- **Baús**: Diário grátis (24h), Caçada (drop 20% em hunt), Nobre (50💎), Relíquia (100💎)
- **Moedas**: Ferro (base), Prata (100F), Ouro (100P), Diamantes (premium)

### Contexto Material Original (Mushoku Tensei)

**Lore Essencial para Coerência:**
- **Reencarnação**: Protagonista morre no Japão e reencarna no mundo de 6 faces com memórias intactas
- **Sistema de Magia**: Baseado em círculos de mana, requer entoação (exceto Conjuração Silenciosa - Voiceless Incantation)
- **Ranks de Magia**: Iniciante, Intermediário, Avançado, Santo, Rei, Imperial, Divino (canônico)
- **3 Grandes Estilos de Espada**:
  - **Deus da Espada (Sword God Style)**: Velocidade extrema, finalização instantânea, "Longsword of Light" (Espada de Luz)
  - **Deus da Água (Water God Style)**: Defesa absoluta, contra-ataque perfeito, fluxo contínuo, "Water Reflection"
  - **Deus do Norte (North God Style)**: Estilo pragmático, fintas, arremessos, esquivas, truques sujos
- **Touki (Manto de Mana)**: Revestimento do corpo com mana para aumentar atributos físicos e defender. Guerreiros avançados usam inconscientemente.
- **Olho Demoníaco (Demon Eye)**: Premonição (ver futuro imediato/esquivar), Clarividência (ver através de obstáculos), Identificação (ver status)
- **Raças**:
  - **Humano**: Equilibrado, adaptável
  - **Migurd (Demônio)**: Cabelo azul, telepatia racial, longevidade, alta afinidade mágica
  - **Superd (Demônio)**: Cabelo verde, joia na testa, terceito olho, mestres de lança, guerreiros temidos
  - **Homem-Fera**: Orelhas/cauda, sentidos aguçados, velocidade/força física
  - **Elfo**: Sensibilidade a mana, pontaria, longevidade, magia natural
  - **Anão**: Metalurgia, constituição física, resistência, mestria em equipamentos
- **Continentes**: Central (Asura, Fittoa), Demônio (Rikarisu), Milis (Milishion), Begaritt (Labirintos/Deserto)
- **Universidade de Magia de Ranoa**: Centro de conhecimento mágico no Reino de Asura
- **Deus Dragão Orsted**, **Técnica Deus (Deus da Espada - Gal Farion), Deus da Água (Jino Britts), Deus do Norte (Alexander)**

---

## DIRETRIZES, MÉTODOS E DETALHES DO PROJETO

### Padrões de Código
- **Async/Await**: Todas as operações de I/O (database, Telegram API) são assíncronas
- **Type Hints**: Obrigatórios em todas as funções públicas
- **Dataclasses**: Models usam `@dataclass` com `to_dict()`/`from_dict()` para serialização
- **Class Methods**: Systems usam `@classmethod` para operações stateless
- **Error Handling**: Try/except com logging, fallbacks graciosos, mensagens de erro amigáveis
- **Persistência Atômica**: `tempfile.NamedTemporaryFile` + `os.replace()` para evitar corrupção

### Nomenclatura de Callbacks
```
# Menus principais: ^nome_menu$
hub_main, profile, inventory_menu, guild_main, explore_menu, crafting_main, market_main, inn_main, training_main, lootbox_main, dungeon_main, party_main, travel_menu, upgrade_menu, skills_menu, stat_distribute_menu, equipments_menu

# Ações com parâmetro: ^prefixo_parametro$
race_{race_key}, vocation_{voc_key}, add_stat_{stat}, equip_item_{id}, use_item_{id}
accept_quest_{id}, claim_quest_{id}
craft_cat_{category}, craft_exec_{recipe_id}, up_lvl_{instance_id}, up_rune_{instance_id}, sock_{instance_id}_{rune_id}
mkt_{filter}, mkt_buy_{listing_id}, mkt_cancel_{listing_id}, mkt_sell_{type}_{id}_{price}
hunt_current, travel_{region_id}, travel_locked_{region_id}
inn_rest_simple, inn_rest_luxury, inn_rest_diamonds
train_sword, train_magic, train_touki
dungeon_create, dungeon_join, dungeon_start_{id}, dungeon_cancel_{id}, dungeon_leave_{id}, dungeon_attack_{id}, dungeon_next_wave_{id}, dungeon_potion_{id}, dungeon_info_{id}
party_create, party_invite, party_invites, party_accept_{id}, party_decline_{id}, party_leave, party_kick, party_disband, party_transfer, party_funds, party_deposit, party_withdraw, party_info_{id}
open_box_{box_id}
```

### Estados de Conversação (ConversationHandler)
- `/start` -> `ASK_NAME` (recebe nome) -> `CHOOSE_RACE` (callback race_) -> `CHOOSE_VOCATION` (callback vocation_) -> Hub

### Roteamento de Texto (callback_router.py -> route_text_input)
Estados em `context.user_data`:
- `awaiting_name` -> `receive_name` (login_system)
- `dungeon_creating` -> `dungeon_process_create` (senha 4 dígitos)
- `dungeon_joining` -> `dungeon_process_join` (ID + senha)
- `party_creating` -> `party_process_create` (nome grupo)
- `party_invite_target` -> `party_process_invite` (Chat ID)
- `party_kick_target` -> `party_process_kick` (Chat ID)
- `party_transfer_target` -> `party_process_transfer` (Chat ID)
- `party_deposit_amount` -> `party_process_deposit` (valor)
- `party_withdraw_amount` -> `party_process_withdraw` (valor)

### Templates de Texto (content/texts/)
Usam `TextLoader.load("arquivo.txt", **kwargs)` com placeholders `{variavel}`. Sempre verificar se todas as variáveis usadas no template são passadas no handler.

### Imagens
Referenciadas por nome em `MessageManager.send_or_edit(image_path="nome.jpg")`. Devem existir em `content/images/`.

### Testes
- Rodar: `python -m pytest tests/ -v`
- Testes cobrem: missões por região, monsters válidos, métodos diários, board de missões, aceitação/limite, regex patterns, serialização, repo assíncrono

---

## TAREFAS

### CONCLUÍDAS

[X][07/09/2026 - 14:30:00] Correção do limite diário de missões (3 -> 2) em quest_system.py e guild_quests.txt
[X][07/09/2026 - 14:35:00] Adição do handler party_info_callback para callback party_info_{party_id}
[X][07/09/2026 - 14:45:00] Adição de 30+ monstros faltantes em monsters.json (regiões + dungeons iniciais)
[X][07/09/2026 - 15:00:00] Adição de 45+ itens faltantes referenciados como drops de monstros em items.json
[X][07/09/2026 - 15:10:00] Correção da estrutura JSON de monsters.json (monsters aninhados corretamente)
[X][07/09/2026 - 15:15:00] Validação completa: todos os testes passam (8/8), imports OK, dados consistentes
[X][07/09/2026 - 15:45:00] Adição de Party, Travel, Dungeon ao Hub Menu (hub_menu.py)
[X][07/09/2026 - 15:50:00] Padronização de navegação: todos os menus com "Voltar" e "Menu Principal"
[X][07/09/2026 - 15:55:00] Correção de exploration_menu.py, travel_menu.py, dungeon_menu.py, party_menu.py
[X][07/09/2026 - 16:00:00] Verificação completa: 72 handlers registrados, todos botões funcionais, testes passando
[X][07/09/2026 - 16:15:00] Correção do erro AttributeError: PlayerRepository.get_player_sync - adicionado método público em player_repo.py
[X][07/09/2026 - 16:20:00] Adicionado error handler global no main.py para capturar e logar exceções não tratadas
[X][07/09/2026 - 16:45:00] Implementado sistema de solicitação de entrada em Party (players podem pedir para entrar em grupos públicos)
[X][07/09/2026 - 17:00:00] Dungeon join simplificado - lista dungeons da região atual e pede apenas senha
[X][07/09/2026 - 17:30:00] Implementadas 120 missões para 6 novas regiões (Roitree, Asura, Milis, Sharia, Begaritt, Wind Port) - total 160 quests
[X][07/09/2026 - 18:00:00] Correção do botão dungeon_join_select - handler registrado no main.py
[X][07/09/2026 - 18:30:00] Persistência de Party implementada - PartyRepository criado, Party movido para models/party.py, dados salvos em disco

### PROBLEMAS
- /home/Arthurvs01/Projetos/MTRPG/world/party_menu.py:162: RuntimeWarning: coroutine 'PartySystem.create_party' was never awaited
  success, msg, party = PartySystem.create_party(player, name)
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
2026-09-07 17:00:13,935 - [ERROR] - __main__: Exception while handling an update: cannot unpack non-iterable coroutine object
Traceback (most recent call last):
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_application.py", line 1315, in process_update
    await coroutine
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_handlers/basehandler.py", line 159, in handle_update
    return await self.callback(update, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/Arthurvs01/Projetos/MTRPG/core/callback_router.py", line 109, in route_text_input
    await party_process_create(update, context)
  File "/home/Arthurvs01/Projetos/MTRPG/world/party_menu.py", line 162, in party_process_create
    success, msg, party = PartySystem.create_party(player, name)
    ^^^^^^^^^^^^^^^^^^^
TypeError: cannot unpack non-iterable coroutine object
2026-09-07 17:00:13,991 - [ERROR] - telegram.ext.Application: An error was raised and an uncaught error was raised while handling the error with an error_handler.
Traceback (most recent call last):
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_application.py", line 1315, in process_update
    await coroutine
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_handlers/basehandler.py", line 159, in handle_update
    return await self.callback(update, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/Arthurvs01/Projetos/MTRPG/core/callback_router.py", line 109, in route_text_input
    await party_process_create(update, context)
  File "/home/Arthurvs01/Projetos/MTRPG/world/party_menu.py", line 162, in party_process_create
    success, msg, party = PartySystem.create_party(player, name)
    ^^^^^^^^^^^^^^^^^^^
TypeError: cannot unpack non-iterable coroutine object

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_application.py", line 1928, in process_error
    await callback(update, context)
  File "/home/Arthurvs01/Projetos/MTRPG/main.py", line 300, in error_handler
    if isinstance(update, Update) and update.effective_message:
                          ^^^^^^
NameError: name 'Update' is not defined. Did you mean: 'update'?

- 2026-09-07 17:05:17,097 - [ERROR] - __main__: Exception while handling an update: 'NoneType' object has no attribute 'reply_text'
Traceback (most recent call last):
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_application.py", line 1315, in process_update
    await coroutine
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_handlers/basehandler.py", line 159, in handle_update
    return await self.callback(update, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/Arthurvs01/Projetos/MTRPG/world/dungeon_menu.py", line 329, in dungeon_start
    await dungeon_attack(update, context)
  File "/home/Arthurvs01/Projetos/MTRPG/world/dungeon_menu.py", line 390, in dungeon_attack
    await update.message.reply_text("Dungeon não está ativa.")
          ^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'reply_text'
2026-09-07 17:05:17,156 - [ERROR] - telegram.ext.Application: An error was raised and an uncaught error was raised while handling the error with an error_handler.
Traceback (most recent call last):
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_application.py", line 1315, in process_update
    await coroutine
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_handlers/basehandler.py", line 159, in handle_update
    return await self.callback(update, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/Arthurvs01/Projetos/MTRPG/world/dungeon_menu.py", line 329, in dungeon_start
    await dungeon_attack(update, context)
  File "/home/Arthurvs01/Projetos/MTRPG/world/dungeon_menu.py", line 390, in dungeon_attack
    await update.message.reply_text("Dungeon não está ativa.")
          ^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'reply_text'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_application.py", line 1928, in process_error
    await callback(update, context)
  File "/home/Arthurvs01/Projetos/MTRPG/main.py", line 300, in error_handler
    if isinstance(update, Update) and update.effective_message:
                          ^^^^^^
NameError: name 'Update' is not defined. Did you mean: 'update'?

- 2026-09-07 17:25:12,765 - [ERROR] - __main__: Exception while handling an update: invalid literal for int() with base 10: 'fur'
Traceback (most recent call last):
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_application.py", line 1315, in process_update
    await coroutine
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_handlers/basehandler.py", line 159, in handle_update
    return await self.callback(update, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/Arthurvs01/Projetos/MTRPG/world/market_menu.py", line 289, in market_sell_item_action
    price = int(parts[4])
ValueError: invalid literal for int() with base 10: 'fur'
2026-09-07 17:25:12,798 - [ERROR] - telegram.ext.Application: An error was raised and an uncaught error was raised while handling the error with an error_handler.
Traceback (most recent call last):
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_application.py", line 1315, in process_update
    await coroutine
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_handlers/basehandler.py", line 159, in handle_update
    return await self.callback(update, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/Arthurvs01/Projetos/MTRPG/world/market_menu.py", line 289, in market_sell_item_action
    price = int(parts[4])
ValueError: invalid literal for int() with base 10: 'fur'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/Arthurvs01/Projetos/MTRPG/.venv/lib/python3.13/site-packages/telegram/ext/_application.py", line 1928, in process_error
    await callback(update, context)
  File "/home/Arthurvs01/Projetos/MTRPG/main.py", line 300, in error_handler
    if isinstance(update, Update) and update.effective_message:
                          ^^^^^^
NameError: name 'Update' is not defined. Did you mean: 'update'?

### PENDENTES

[ ][                     ] Itens e Equipamentos não devem possuir valor predefinido, cada player decide por quanto ira vender seus itens e equipamentos e no caso dos itens decide tambem a quantidade
[ ][                     ] Somente deve ser possivel aceitar missões da região em que estiver
[ ][                     ] Adicionar monstros das dungeons avançadas (Asura, Milis, Sharia, Begaritt, Demon King, Sunken City)
[ ][                     ] Implementar sistema de aprendizado de skills (espada/magia) via menus
[ ][                     ] Adicionar mais feitiços (ranks Intermediário a Divino para todas escolas)
[ ][                     ] Implementar técnicas de espada dos ranks Avançado a Divino
[ ][                     ] Criar sistema de craft de runas (não apenas dropar/comprar)
[ ][                     ] Implementar marketplace NPC (guild_shop.txt existe mas não há handler)
[ ][                     ] Adicionar sistema de encantamento de equipamentos além de runas
[ ][                     ] Implementar PvP / Arena entre players
[ ][                     ] Sistema de reputação/fação além de guild points
[ ][                     ] Eventos sazonais / world bosses
[ ][                     ] Sistema de mounts / viagem rápida
[ ][                     ] Sistema de craft de consumíveis (poções, pergaminhos)
[ ][                     ] Implementar skill trees visuais no menu de skills
[ ][                     ] Adicionar sistema de títulos/conquistas
[ ][                     ] Implementar trade direto entre players (fora do mercado)
[ ][                     ] Guild wars / conflito entre grupos
[ ][                     ] Dungeons solo / instâncias pessoais
[ ][                     ] Logs estruturados (JSON) para debugging
[ ][                     ] Métricas de uso (comandos mais usados, funis de conversão)
[ ][                     ] Rate limiting / anti-spam nos handlers
[ ][                     ] Backup automático do database
[ ][                     ] Migração de dados para SQLite/PostgreSQL se escala
[ ][                     ] Webhook mode para produção (ao invés de polling)
[ ][                     ] Admin panel / comandos de GM
[ ][                     ] Sistema de relatórios de bugs in-game

---

## RECOMENDAÇÕES DE TAREFAS FUTURAS

### Prioridade Alta (Core Gameplay)


### Prioridade Média (Sistemas de Progressão)


### Prioridade Baixa (Conteúdo Social/Endgame)


### Qualidade de Vida / Técnico


---

## NOTAS DE DESENVOLVIMENTO

- **Sempre validar**: Após qualquer mudança em callbacks, verificar se `main.py` tem o handler registrado
- **Templates**: Ao adicionar variável num template `.txt`, atualizar TODOS os handlers que o chamam
- **Monstros**: Ao adicionar região/dungeon, adicionar monstros em `monsters.json` E itens de drop em `items.json`
- **Skills**: Sistema de aprendizado existe (`SwordSystem`, `MagicSystem`) mas falta UI para gastar pontos/XP
- **Balanceamento**: Valores de XP, moedas, drops são placeholders - precisa playtest
- **Imagens**: Muitos menus referenciam imagens que podem não existir em `content/images/`