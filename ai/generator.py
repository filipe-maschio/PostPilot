import random
import re
import os
from dotenv import load_dotenv
from openai import OpenAI

from utils.storage import load_posts, load_themes, save_theme
from utils.formatter import clean_text
from utils.storage import save_post_with_metadata

# 🔐 Load environment variables
load_dotenv()

client = OpenAI()

# =========================
# AI CACHE
# =========================

# Cache to avoid repeated API calls (cost + latency optimization)
score_cache = {}
idea_cache = {}


# =========================
# CONFIGURATION
# =========================

MAX_WORDS = 160
NUM_POSTS_TO_GENERATE = 5
NUM_POSTS_TO_RETURN = 3


# =========================
# PROMPT BUILDER
# =========================

def build_prompt():
    return f"""
Você é um especialista em cibersegurança que cria conteúdo para LinkedIn.

Seu objetivo é escrever posts que geram engajamento real (comentários, salvamentos e compartilhamentos), altamente engajante, natural e pronto para copiar e colar.  

SEU ESTILO:

- Direto e sem enrolação
- Baseado em problemas reais
- Focado no que acontece na prática
- Explica de forma simples
- Evita teoria excessiva

ESTILO DE RACIOCÍNIO:

- "Na prática..."
- "O problema não é X, é Y"
- "A maioria das empresas erra aqui"
- "Isso parece simples, mas..."

PADRÕES DE ESCRITA (MUITO IMPORTANTE):

- Use contraste:
  Ex: "A maioria acha X. Mas o problema é Y."
- Destaque problemas reais e básicos, não apenas ataques sofisticados
- Use listas para tornar o conteúdo prático
- Use frases curtas e diretas (1 linha por ideia)
- Use repetição intencional para reforçar ideia:
  Ex: "Começa com processo. Começa com disciplina."
- Inclua um insight forte ou virada de perspectiva
- Termine com uma pergunta que gere reflexão

REGRAS GERAIS:

- Máximo {MAX_WORDS} palavras  
- Linguagem simples e natural  
- Tom profissional, mas humano  
- Evitar jargões técnicos excessivos
- Não soar robótico ou genérico
- NÃO usar frases genéricas  
- Escrever como um profissional experiente
- NÃO usar emojis  

ESTRUTURA OBRIGATÓRIA:

1. Gancho forte na primeira linha
2. Desenvolvimento com valor real
3. Insight ou reflexão
4. Fechamento com pergunta

FORMATAÇÃO (MUITO IMPORTANTE):

- Usar linhas curtas
- Quebrar linhas com frequência
- Espaçamento entre blocos de texto
- Listas com "-" (hífen)
- NÃO usar parágrafos longos
- O texto deve ser agradável visualmente no LinkedIn

VARIAÇÃO:

- Cada post deve abordar um problema diferente
- NÃO repetir estrutura (lista vs reflexão vs narrativa)
- NÃO usar o mesmo tipo de abertura

TIPOS DE POST:

1. EDUCATIVO:
- Ensinar algo prático
- Pode usar lista (3 ou 5 itens)
- Foco em utilidade

2. OPINIÃO:
- Ponto de vista forte
- Pode questionar práticas comuns
- Estimular debate

3. NOTÍCIA (SE FOR USADA):
- NÃO resumir a notícia
- Explicar o impacto
- Trazer análise própria

4. EXPERIÊNCIA:
- Aprendizado real
- Pode incluir erro ou descoberta

HASHTAGS:

- Adicionar de 4 a 6 hashtags no final
- Exemplo:
#CyberSecurity #InfoSec #TI #SegurançaDaInformação #Cibersegurança

EVITAR:
- Frases genéricas como "segurança é importante"
- Conteúdo óbvio
- Texto longo demais
- Repetição de ideias

IMPORTANTE:
- Cada post deve ter uma ideia única
- Não repetir temas entre os posts

TAREFA:

Gere {NUM_POSTS_TO_GENERATE} posts.

Distribuição:
- 1 educativo
- 1 opinião
- restante variado

FORMATO DE SAÍDA:

POST 1:
(conteúdo)

POST 2:
(conteúdo)

POST 3:
(conteúdo)
"""

# =========================
# GENERATE POSTS
# =========================

def generate_posts():
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": build_prompt()}],
    )

    return parse_posts(response.choices[0].message.content)


# =========================
# PARSE POSTS (ROBUST)
# =========================

def parse_posts(text):
    posts = []

    # Split using regex to handle variations like POST 1:, POST1:, etc.
    chunks = re.split(r"POST\s*\d*:", text)

    for chunk in chunks:
        content = clean_text(chunk.strip())

        if not content:
            continue

        if len(content.split()) < 20:
            continue

        posts.append(content)

    return posts


# =========================
# THEME EXTRACTION
# =========================

def extract_theme(post):
    prompt = f"""
    Qual é o tema principal deste post?

    Responda com 1 ou 2 palavras em português.

    Exemplos:
    phishing, senhas, ransomware, backup, acesso

    POST:
    {post}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return response.choices[0].message.content.strip().lower().split("\n")[0]

    except:
        return "general"


# Cache layer to avoid repeated API calls
def get_theme(post, cache):
    if post in cache:
        return cache[post]

    theme = extract_theme(post)
    cache[post] = theme
    return theme


# =========================
# IDEA SIMILARITY CHECK (AI)
# =========================

def is_same_idea_with_ai(post, history):

    for old in history[-3:]:

        key = (post, old)

        # Check cache first
        if key in idea_cache:
            if idea_cache[key]:
                return True
            continue

        prompt = f"""
        Os dois posts abaixo expressam a MESMA IDEIA?

        Responda apenas: SIM ou NÃO

        POST A:
        {post}

        POST B:
        {old}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            answer = response.choices[0].message.content.upper()

            result = "SIM" in answer

            # Save result in cache
            idea_cache[key] = result

            if result:
                return True

        except Exception as e:
            print(f"[AI IDEA ERROR] {e}")

    return False


# =========================
# QUICK SCORE (NO AI)
# =========================

def quick_score(post):
    score = 0

    if len(post.split("\n")[0]) < 80:
        score += 2

    if "-" in post:
        score += 2

    if "?" in post[-100:]:
        score += 2

    if 50 < len(post.split()) < 130:
        score += 2

    return score


# =========================
# AI SCORING
# =========================

def score_post_with_ai(post):

    if post in score_cache:
        return score_cache[post]

    prompt = f"""
Avalie este post de LinkedIn com base nos critérios abaixo.

Dê notas de 0.0 a 10.0 para cada critério:

1. Hook (o início prende atenção?)
2. Clareza (é fácil de ler e entender?)
3. Valor (ensina algo útil ou traz insight?)
4. Originalidade (evita ser genérico?)
5. Engajamento (gera vontade de comentar?)

POST:
{post}

Agora calcule a média final.

Regras:
- Use números decimais
- NÃO inclua explicações

Formato obrigatório:

HOOK: X.X
CLAREZA: X.X
VALOR: X.X
ORIGINALIDADE: X.X
ENGAJAMENTO: X.X
FINAL: X.X
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        text = response.choices[0].message.content

        scores = {}

        for line in text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().upper()
                value = value.strip().replace(",", ".")

                try:
                    scores[key] = float(value)
                except:
                    continue

        # fallback structure
        result = {
            "hook": scores.get("HOOK", 5.0),
            "clareza": scores.get("CLAREZA", 5.0),
            "valor": scores.get("VALOR", 5.0),
            "originalidade": scores.get("ORIGINALIDADE", 5.0),
            "engajamento": scores.get("ENGAJAMENTO", 5.0),
            "final": scores.get("FINAL", 5.0),
        }

        score_cache[post] = result
        return result

    except:
        fallback = {
            "hook": 5.0,
            "clareza": 5.0,
            "valor": 5.0,
            "originalidade": 5.0,
            "engajamento": 5.0,
            "final": 5.0,
        }

    score_cache[post] = fallback
    return fallback


# =========================
# FINAL SCORING
# =========================

def score_post(post, ai_scores=None):
    score = 0

    if len(post.split("\n")[0]) < 80:
        score += 2

    if "-" in post:
        score += 2

    if "?" in post[-100:]:
        score += 2

    if 50 < len(post.split()) < 130:
        score += 2

    # Use precomputed AI scores if available
    if ai_scores is None:
        ai_scores = score_post_with_ai(post)

    score += ai_scores["final"] * 0.7

    return score


# =========================
# SIMILARITY
# =========================

def similarity(a, b):
    a_words = set(a.lower().split())
    b_words = set(b.lower().split())

    if not a_words or not b_words:
        return 0

    return len(a_words & b_words) / len(a_words | b_words)


def is_too_similar(post, history):
    for old in history[-5:]:
        if similarity(post, old) > 0.7:
            return True
    return False


# =========================
# SELECT BEST POSTS
# =========================

def select_best_posts(posts):

    raw_history = load_posts()

    # Normalize history (handle dict and string formats)
    history = [
        p["post"] if isinstance(p, dict) else p
        for p in raw_history
    ]

    themes = load_themes()

    scored = []
    theme_cache = {}

    # =========================
    # PHASE 1 — FAST FILTER (NO AI)
    # =========================
    # Goal: eliminate bad/repeated posts using cheap operations only

    candidates = []

    for post in posts:

        # Skip if text is too similar to recent posts
        if is_too_similar(post, history):
            continue

        # Get theme using cache (avoids repeated API calls)
        theme = get_theme(post, theme_cache)

        # Skip if theme was already used recently
        if theme in themes:
            continue

        # Quick heuristic score (no AI)
        score = quick_score(post)
        candidates.append((post, score))

    # Fallback if everything was filtered
    if not candidates:
        return posts[:NUM_POSTS_TO_RETURN]

    # Select top candidates based on quick score
    candidates.sort(key=lambda x: x[1], reverse=True)
    top_candidates = [p[0] for p in candidates[:3]]

    # =========================
    # PHASE 2 — AI VALIDATION
    # =========================
    # Goal: apply expensive checks only on best candidates

    final = []

    for post in top_candidates:

        # Check semantic similarity (idea-level duplication)
        if is_same_idea_with_ai(post, history):
            continue

        # 🔥 Get full AI scoring (with detailed criteria)
        ai_scores = score_post_with_ai(post)

        # 🔥 Compute final combined score (rules + AI)
        score = score_post(post, ai_scores)

        # Store everything (post + score + metadata)
        final.append((post, score, ai_scores))

    # Fallback if AI filtered everything
    if not final:
        return top_candidates

    # Final ranking
    final.sort(key=lambda x: x[1], reverse=True)

    # =========================
    # SAVE RESULTS
    # =========================
    # Save both themes and detailed scoring metadata

    best_posts = []

    for post, score, ai_scores in final[:NUM_POSTS_TO_RETURN]:
        best_posts.append(post)

        # Save theme using cache
        theme = theme_cache.get(post)
        if theme:
            save_theme(theme)

        # Save post with metadata
        save_post_with_metadata(post, ai_scores)

    return best_posts


# =========================
# MAIN
# =========================

def generate_best_posts():
    posts = generate_posts()
    return select_best_posts(posts)