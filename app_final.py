# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, redirect, url_for
import json
import os

app = Flask(__name__)
DATA_FILE = 'tasks.json'

def inicializar_dados():
    default_data = {
        "brain_dump": [], 
        "foco_hoje": [], 
        "concluido": [],
        "metas_smart": [],
        "livros": [],
        "filmes": [],
        "anotacoes_midia": "",
        "meta_livros_quero": 10,
        "meta_filmes_quero": 20,
        # Estrutura Financeira
        "saldo_inicial": 0.0,
        "entradas": [],       
        "gastos_fixos": [],   
        "gastos_variaveis": [],
        "quero": [],          
        "preciso": []         
    }
    if not os.path.exists(DATA_FILE):
        return default_data
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            dados = json.load(f)
        except json.JSONDecodeError:
            return default_data
            
    # Garante retrocompatibilidade para as novas chaves
    for chave, valor in default_data.items():
        if chave not in dados:
            dados[chave] = valor
    return dados

def ler_dados():
    return inicializar_dados()

def salvar_dados(dados):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# CSS & HTML - Edição Definitiva com Paleta Brisa Solar e SMART Completo
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meu Dopamine Dashboard ⚡</title>
    <style>
        :root {
            --bg-color: #FAF6F0; /* Bege Acolhedor */
            --card-bg: #FFFFFF;
            --text-main: #3D261C; /* Chocolate Brown */
            --text-muted: #7A695E;
            --accent-terracotta: #D46A43; /* Terracota */
            --accent-peach: #F3B391; /* Pêssego Suave */
            --accent-green: #81B29A; /* Verde Sálvia */
            --accent-red: #E07A5F; 
            --border-color: #EADEC9;
            --star-color: #F4C430;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        header {
            text-align: center;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 2.2rem;
            margin-bottom: 5px;
            color: var(--accent-terracotta);
            font-weight: 700;
        }

        .subtitle {
            color: var(--text-muted);
            margin-top: 0;
            font-size: 1rem;
        }

        /* Abas */
        .nav-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
            width: 100%;
            max-width: 1050px;
        }

        .tab-btn {
            background-color: #EFE6D8;
            border: none;
            padding: 12px 22px;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 600;
            color: var(--text-main);
            transition: all 0.2s ease;
        }

        .tab-btn.active {
            background-color: var(--accent-terracotta);
            color: white;
            box-shadow: 0 4px 10px rgba(212, 106, 67, 0.25);
        }

        .tab-content {
            display: none;
            width: 100%;
            max-width: 1050px;
        }

        .tab-content.active {
            display: block;
        }

        /* Diário */
        .board {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(310px, 1fr));
            gap: 20px;
            width: 100%;
        }

        .column {
            background-color: rgba(255, 255, 255, 0.65);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(61, 38, 28, 0.02);
            border: 1px solid var(--border-color);
        }

        .column h2 {
            font-size: 1.25rem;
            margin-top: 0;
            margin-bottom: 15px;
            color: var(--text-main);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .card {
            background-color: var(--card-bg);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 12px;
            box-shadow: 0 2px 6px rgba(61,38,28,0.03);
            border-left: 5px solid var(--accent-peach);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .column-foco .card { border-left-color: var(--accent-terracotta); }
        .column-concluido .card { border-left-color: var(--accent-green); opacity: 0.7; text-decoration: line-through; }

        .card p { margin: 0; font-size: 0.95rem; line-height: 1.4; }

        .card-actions { display: flex; justify-content: flex-end; gap: 8px; }

        .btn-action {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 0.85rem;
            padding: 6px 12px;
            border-radius: 6px;
            transition: background 0.2s;
        }

        .btn-move { background-color: #F3EAE0; color: var(--text-main); }
        .btn-done { background-color: rgba(129, 178, 154, 0.2); color: #4f7a64; font-weight: bold; }
        .btn-delete { background-color: rgba(212, 106, 67, 0.1); color: var(--accent-terracotta); }

        .quick-capture { width: 100%; margin-bottom: 30px; }
        .quick-capture form { display: flex; gap: 10px; }
        .quick-capture input[type="text"] {
            flex: 1;
            padding: 15px;
            border: 2px solid var(--border-color);
            border-radius: 12px;
            font-size: 1rem;
            outline: none;
            background-color: var(--card-bg);
        }
        .quick-capture button {
            background-color: var(--accent-terracotta);
            color: white;
            border: none;
            padding: 0 25px;
            border-radius: 12px;
            font-weight: bold;
            cursor: pointer;
        }

        /* --- SESSÃO METAS SMART (VERSÃO COMPLETA) --- */
        .smart-container {
            background-color: var(--card-bg);
            padding: 25px;
            border-radius: 16px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 15px rgba(0,0,0,0.02);
        }

        .smart-header-guide {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
            margin-bottom: 25px;
        }

        .smart-badge {
            text-align: center;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 0.85rem;
            color: white;
        }

        .badge-s { background-color: #5C3D2E; }
        .badge-m { background-color: #8C533C; }
        .badge-a { background-color: #BE785C; }
        .badge-r { background-color: #D49077; }
        .badge-t { background-color: #E6B6A5; }

        .smart-form {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }

        .form-section {
            border: 1px solid var(--border-color);
            padding: 18px;
            border-radius: 10px;
            background-color: #FAF9F6;
        }

        .form-section h3 {
            margin-top: 0;
            margin-bottom: 12px;
            font-size: 1rem;
            color: var(--accent-terracotta);
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 5px;
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 10px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        .form-group label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
        }

        .form-group input, .form-group textarea {
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            font-family: inherit;
            font-size: 0.9rem;
        }

        .form-group textarea {
            resize: vertical;
            height: 60px;
        }

        .btn-submit-smart {
            background-color: var(--accent-terracotta);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            font-size: 1rem;
            margin-top: 10px;
        }

        .active-goals-list {
            margin-top: 30px;
        }

        .goal-item {
            background-color: #FAF9F6;
            border-left: 6px solid var(--accent-terracotta);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border: 1px solid var(--border-color);
            border-left-width: 6px;
        }

        .goal-item-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }

        .goal-title {
            font-size: 1.15rem;
            font-weight: bold;
            color: var(--accent-terracotta);
            margin: 0;
        }

        .goal-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
            font-size: 0.9rem;
        }

        .goal-sub-box {
            background: white;
            padding: 12px;
            border-radius: 6px;
            border: 1px dashed var(--border-color);
        }

        .goal-sub-box strong {
            color: var(--text-main);
            display: block;
            margin-bottom: 5px;
            font-size: 0.8rem;
            text-transform: uppercase;
        }

        .steps-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
        }

        .steps-table th, .steps-table td {
            border: 1px solid var(--border-color);
            padding: 8px;
            text-align: left;
            font-size: 0.85rem;
        }

        .steps-table th {
            background-color: #F3EAE0;
        }

        /* --- FILMES E LEITURAS --- */
        .shelf-form {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        .shelf-form input[type="text"] {
            flex: 2;
            min-width: 180px;
            padding: 10px 12px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }

        .shelf-form select {
            flex: 1;
            min-width: 100px;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: white;
        }

        .shelf-form button {
            background-color: var(--accent-terracotta);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: bold;
            cursor: pointer;
        }

        .media-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 10px;
            border-bottom: 1px dashed var(--border-color);
            transition: background 0.2s;
        }

        .media-item:hover {
            background-color: rgba(243, 179, 145, 0.08);
        }

        .media-item.concluido span {
            text-decoration: line-through;
            color: var(--text-muted);
        }

        .stars {
            color: var(--star-color);
            font-size: 1.1rem;
            letter-spacing: 2px;
        }

        .media-sidebar {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .stat-badge-box {
            background: linear-gradient(135deg, var(--accent-peach) 0%, #FAF6F0 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            color: var(--text-main);
        }

        .stat-number {
            font-size: 2.2rem;
            font-weight: 800;
            color: var(--accent-terracotta);
            margin: 5px 0;
        }

        .top5-box {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
        }

        .top5-box h3 {
            color: var(--text-main);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
            margin-top: 0;
        }

        .top5-list {
            padding-left: 20px;
            margin-bottom: 0;
        }

        .top5-list li {
            margin-bottom: 8px;
            font-weight: 500;
        }

        .notes-textarea {
            width: 100%;
            height: 150px;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 12px;
            font-family: inherit;
            resize: none;
            box-sizing: border-box;
            background-color: #FAF9F6;
        }

        .btn-save-notes {
            background-color: var(--text-main);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            margin-top: 8px;
        }

        /* --- SESSÃO FINANCEIRA --- */
        .fin-layout {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 25px;
            width: 100%;
        }

        @media (max-width: 900px) {
            .fin-layout { grid-template-columns: 1fr; }
        }

        .fin-column {
            background-color: var(--card-bg);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 15px rgba(0,0,0,0.01);
            margin-bottom: 25px;
        }

        .fin-title {
            color: var(--accent-terracotta);
            border-bottom: 2px solid var(--accent-peach);
            padding-bottom: 8px;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }

        .fin-form {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }

        .fin-form input[type="text"] {
            flex: 2;
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }

        .fin-form input[type="number"] {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }

        .fin-form button {
            background-color: var(--accent-terracotta);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 15px;
            font-weight: bold;
            cursor: pointer;
        }

        .fin-list {
            width: 100%;
            margin-top: 10px;
        }

        .fin-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 5px;
            border-bottom: 1px dashed var(--border-color);
            font-size: 0.95rem;
        }

        .resumo-box {
            background: #FFFDF9;
            border: 2px solid var(--accent-terracotta);
            border-radius: 16px;
            padding: 20px;
        }

        .resumo-title {
            text-align: center;
            margin-top: 0;
            color: var(--accent-terracotta);
            font-weight: bold;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }

        .resumo-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #FAF6F0;
            font-weight: 500;
        }

        .saldo-final-box {
            margin-top: 15px;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-size: 1.25rem;
            font-weight: bold;
        }

        .saldo-positivo {
            background-color: rgba(129, 178, 154, 0.2);
            color: #3b634e;
            border: 1px solid var(--accent-green);
        }

        .saldo-negativo {
            background-color: rgba(224, 122, 95, 0.15);
            color: #a64b32;
            border: 1px solid var(--accent-red);
        }

        .filtro-impulso {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 25px;
        }

        .filtro-box {
            background: #FDFBF7;
            border: 1px dashed var(--accent-peach);
            border-radius: 12px;
            padding: 15px;
        }

        .filtro-box h3 {
            margin-top: 0;
            font-size: 1rem;
            text-align: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
        }

        .filtro-box form {
            display: flex;
            gap: 5px;
            margin-bottom: 10px;
        }

        .filtro-box input {
            flex: 1;
            padding: 6px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            font-size: 0.85rem;
        }

        .filtro-box button {
            background: var(--text-main);
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
        }
    </style>
</head>
<body>

    <header>
        <h1>Meu Espaço Calmo 🧠</h1>
        <p class="subtitle">Organização simplificada para mentes brilhantes e dinâmicas.</p>
    </header>

    <div class="nav-tabs">
        <button class="tab-btn active" id="btn-diario" onclick="switchTab('diario')">⚡ Rotina Diária</button>
        <button class="tab-btn" id="btn-smart" onclick="switchTab('smart')">🎯 Planejador SMART</button>
        <button class="tab-btn" id="btn-midia" onclick="switchTab('midia')">📚 Filmes e Leituras</button>
        <button class="tab-btn" id="btn-financeiro" onclick="switchTab('financeiro')">💰 Controle Financeiro</button>
    </div>

    <!-- ABA 1: ROTINA DIÁRIA -->
    <div id="tab-diario" class="tab-content active">
        <section class="quick-capture">
            <form action="/add" method="POST">
                <input type="text" name="task_text" placeholder="Ideia rápida, tarefa ou lembrete... (Digite e aperte Enter)" required autocomplete="off" autofocus>
                <button type="submit">Guardar</button>
            </form>
        </section>

        <main class="board">
            <div class="column column-dump">
                <h2>Esvaziar a Cabeça 📥</h2>
                {% for task in dados.brain_dump %}
                <div class="card">
                    <p>{{ task }}</p>
                    <div class="card-actions">
                        <a href="/move/brain_dump/foco_hoje/{{ loop.index0 }}"><button class="btn-action btn-move">🎯 Focar Hoje</button></a>
                        <a href="/delete/brain_dump/{{ loop.index0 }}"><button class="btn-action btn-delete">🗑️</button></a>
                    </div>
                </div>
                {% endfor %}
            </div>

            <div class="column column-foco">
                <h2>Foco de Hoje 🎯 <small style="font-size: 0.8rem; font-weight: normal; color: var(--accent-terracotta);">({{ dados.foco_hoje|length }}/3)</small></h2>
                {% if dados.foco_hoje|length == 0 %}
                    <p style="color: var(--text-muted); font-size: 0.9rem; font-style: italic;">Arraste tarefas para cá para começar o seu dia com tranquilidade.</p>
                {% endif %}
                {% for task in dados.foco_hoje %}
                <div class="card">
                    <p>{{ task }}</p>
                    <div class="card-actions">
                        <a href="/move/foco_hoje/concluido/{{ loop.index0 }}"><button class="btn-action btn-done">Feito! 🎉</button></a>
                        <a href="/move/foco_hoje/brain_dump/{{ loop.index0 }}"><button class="btn-action btn-move">↩️ Devolver</button></a>
                    </div>
                </div>
                {% endfor %}
            </div>

            <div class="column column-concluido">
                <h2>Feito hoje 🎉</h2>
                {% for task in dados.concluido %}
                <div class="card">
                    <p>{{ task }}</p>
                    <div class="card-actions">
                        <a href="/delete/concluido/{{ loop.index0 }}"><button class="btn-action btn-delete">Limpar</button></a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </main>
    </div>

    <!-- ABA 2: PLANEJADOR SMART (COMPLETO) -->
    <div id="tab-smart" class="tab-content">
        <div class="smart-container">
            <div class="smart-header-guide">
                <div class="smart-badge badge-s">S - Específica</div>
                <div class="smart-badge badge-m">M - Mensurável</div>
                <div class="smart-badge badge-a">A - Atingível</div>
                <div class="smart-badge badge-r">R - Relevante</div>
                <div class="smart-badge badge-t">T - Temporal</div>
            </div>

            <h2 style="margin-top:0; color: var(--accent-terracotta);">Definir Nova Meta SMART</h2>
            <form action="/add_smart" method="POST" class="smart-form">
                <div class="form-section">
                    <h3>1. Definir a Meta</h3>
                    <div class="form-group">
                        <label for="goal_name">O que você quer alcançar? (Seja específico)</label>
                        <input type="text" id="goal_name" name="goal_name" placeholder="Ex: Estabelecer rotina matinal saudável de 20 min" required>
                    </div>
                </div>

                <div class="form-section">
                    <h3>2. Passos Mensuráveis e Atingíveis</h3>
                    <p style="font-size: 0.8rem; color: #777; margin: 0 0 10px 0;">Quebre em 2 passos rápidos para não sobrecarregar:</p>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Passo 1: Descrição</label>
                            <input type="text" name="step1_desc" placeholder="Ex: Preparar roupas de treino na noite anterior" required>
                        </div>
                        <div class="form-group" style="max-width: 150px;">
                            <label>Tempo Estimado</label>
                            <input type="text" name="step1_time" placeholder="Ex: 5 min" required>
                        </div>
                        <div class="form-group" style="max-width: 150px;">
                            <label>Prazo</label>
                            <input type="text" name="step1_deadline" placeholder="Ex: Hoje à noite" required>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Passo 2: Descrição</label>
                            <input type="text" name="step2_desc" placeholder="Ex: Alongamento leve ao acordar" required>
                        </div>
                        <div class="form-group" style="max-width: 150px;">
                            <label>Tempo Estimado</label>
                            <input type="text" name="step2_time" placeholder="Ex: 10 min" required>
                        </div>
                        <div class="form-group" style="max-width: 150px;">
                            <label>Prazo</label>
                            <input type="text" name="step2_deadline" placeholder="Ex: Amanhã 7:00" required>
                        </div>
                    </div>
                </div>

                <div class="form-section">
                    <h3>3. Planejamento Preventivo (Essencial para TDAH)</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="resources">Recursos Necessários</label>
                            <textarea id="resources" name="resources" placeholder="Ex: Garrafa de água ao lado da cama, despertador longe da cama."></textarea>
                        </div>
                        <div class="form-group">
                            <label for="obstacles">Possível Obstáculo</label>
                            <textarea id="obstacles" name="obstacles" placeholder="Ex: Ficar no celular procrastinando ao acordar."></textarea>
                        </div>
                        <div class="form-group">
                            <label for="plan_obstacles">Como superar esse Obstáculo?</label>
                            <textarea id="plan_obstacles" name="plan_obstacles" placeholder="Ex: Colocar app blocker nas primeiras 2 horas do dia."></textarea>
                        </div>
                    </div>
                </div>

                <div class="form-section">
                    <h3>4. Resultado Desejado</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="success_measurement">Como medirá o sucesso?</label>
                            <input type="text" id="success_measurement" name="success_measurement" placeholder="Ex: Sentir mais energia e completar 4 dias seguidos">
                        </div>
                        <div class="form-group">
                            <label for="achieved_outcome">Resultado Esperado</label>
                            <input type="text" id="achieved_outcome" name="achieved_outcome" placeholder="Ex: Iniciar o dia útil com clareza e sem pressa">
                        </div>
                    </div>
                </div>

                <button type="submit" class="btn-submit-smart">Salvar Meta SMART 🎯</button>
            </form>

            <div class="active-goals-list">
                <h3 style="color: var(--accent-terracotta); border-bottom: 2px solid var(--accent-peach); padding-bottom: 5px;">Minhas Metas SMART Cadastradas</h3>
                {% if dados.metas_smart|length == 0 %}
                    <p style="font-style: italic; color: #777;">Nenhuma meta SMART cadastrada ainda. Que tal criar a primeira acima?</p>
                {% endif %}
                
                {% for meta in dados.metas_smart %}
                <div class="goal-item">
                    <div class="goal-item-header">
                        <h4 class="goal-title">{{ meta.goal_name }}</h4>
                        <a href="/delete_smart/{{ loop.index0 }}"><button class="btn-action btn-delete">Excluir Meta</button></a>
                    </div>

                    <div style="margin-top: 10px;">
                        <strong>Passos Práticos:</strong>
                        <table class="steps-table">
                            <thead>
                                <tr>
                                    <th>Ação</th>
                                    <th>Tempo</th>
                                    <th>Prazo</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>{{ meta.step1_desc }}</td>
                                    <td>{{ meta.step1_time }}</td>
                                    <td>{{ meta.step1_deadline }}</td>
                                </tr>
                                <tr>
                                    <td>{{ meta.step2_desc }}</td>
                                    <td>{{ meta.step2_time }}</td>
                                    <td>{{ meta.step2_deadline }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div class="goal-grid">
                        <div class="goal-sub-box">
                            <strong>Recursos & Apoios</strong>
                            {{ meta.resources or "Nenhum cadastrado" }}
                        </div>
                        <div class="goal-sub-box">
                            <strong>Plano Antifracasso (Obstáculo & Solução)</strong>
                            <span style="color: #c94c4c; font-weight: 500;">Obs:</span> {{ meta.obstacles }} <br>
                            <span style="color: #4c9fc9; font-weight: 500;">Solução:</span> {{ meta.plan_obstacles }}
                        </div>
                        <div class="goal-sub-box">
                            <strong>Como medir o Sucesso</strong>
                            {{ meta.success_measurement }}
                        </div>
                        <div class="goal-sub-box">
                            <strong>Resultado Esperado</strong>
                            {{ meta.achieved_outcome }}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- ABA 3: FILMES E LEITURAS DO ANO -->
    <div id="tab-midia" class="tab-content">
        <div class="media-container">
            <div>
                <!-- Leituras do Ano -->
                <div class="fin-column" style="background-color: var(--card-bg); border-radius:16px; padding:25px; border:1px solid var(--border-color);">
                    <h2 class="shelf-title" style="color:var(--accent-terracotta); border-bottom:2px solid var(--accent-peach); padding-bottom:8px; margin-top:0; margin-bottom:20px; font-size:1.4rem;">📚 Leituras do Ano</h2>
                    <form action="/add_media/livros" method="POST" class="shelf-form">
                        <input type="text" name="titulo" placeholder="Título do livro..." required>
                        <input type="text" name="autor" placeholder="Autor..." required>
                        <select name="nota" required>
                            <option value="" disabled selected>Dar nota...</option>
                            <option value="5">⭐⭐⭐⭐⭐ (Favorito)</option>
                            <option value="4">⭐⭐⭐⭐</option>
                            <option value="3">⭐⭐⭐</option>
                            <option value="2">⭐⭐</option>
                            <option value="1">⭐</option>
                        </select>
                        <button type="submit">Adicionar</button>
                    </form>

                    <div style="margin-top: 15px;">
                        {% if dados.livros|length == 0 %}
                            <p style="font-style: italic; color: var(--text-muted);">Nenhum livro cadastrado ainda.</p>
                        {% endif %}
                        {% for livro in dados.livros %}
                        <div class="media-item {% if livro.concluido %}concluido{% endif %}">
                            <div>
                                <a href="/toggle_media/livros/{{ loop.index0 }}" style="text-decoration: none; font-size: 1.2rem; margin-right: 10px;">
                                    {% if livro.concluido %}✅{% else %}⬜{% endif %}
                                </a>
                                <span><strong>{{ livro.titulo }}</strong> - {{ livro.autor }}</span>
                            </div>
                            <div>
                                <span class="stars">
                                    {% for i in range(livro.nota|int) %}★{% endfor %}
                                </span>
                                <a href="/delete_media/livros/{{ loop.index0 }}" style="margin-left: 15px; text-decoration: none;">🗑️</a>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <!-- Filmes do Ano -->
                <div class="fin-column" style="background-color: var(--card-bg); border-radius:16px; padding:25px; border:1px solid var(--border-color);">
                    <h2 class="shelf-title" style="color:var(--accent-terracotta); border-bottom:2px solid var(--accent-peach); padding-bottom:8px; margin-top:0; margin-bottom:20px; font-size:1.4rem;">🎬 Filmes do Ano</h2>
                    <form action="/add_media/filmes" method="POST" class="shelf-form">
                        <input type="text" name="titulo" placeholder="Nome do filme..." required>
                        <input type="text" name="autor" placeholder="Diretor / Gênero..." required>
                        <select name="nota" required>
                            <option value="" disabled selected>Dar nota...</option>
                            <option value="5">⭐⭐⭐⭐⭐</option>
                            <option value="4">⭐⭐⭐⭐</option>
                            <option value="3">⭐⭐⭐</option>
                            <option value="2">⭐⭐</option>
                            <option value="1">⭐</option>
                        </select>
                        <button type="submit">Adicionar</button>
                    </form>

                    <div style="margin-top: 15px;">
                        {% if dados.filmes|length == 0 %}
                            <p style="font-style: italic; color: var(--text-muted);">Nenhum filme cadastrado ainda.</p>
                        {% endif %}
                        {% for filme in dados.filmes %}
                        <div class="media-item {% if filme.concluido %}concluido{% endif %}">
                            <div>
                                <a href="/toggle_media/filmes/{{ loop.index0 }}" style="text-decoration: none; font-size: 1.2rem; margin-right: 10px;">
                                    {% if filme.concluido %}✅{% else %}⬜{% endif %}
                                </a>
                                <span><strong>{{ filme.titulo }}</strong> - {{ filme.autor }}</span>
                            </div>
                            <div>
                                <span class="stars">
                                    {% for i in range(filme.nota|int) %}★{% endfor %}
                                </span>
                                <a href="/delete_media/filmes/{{ loop.index0 }}" style="margin-left: 15px; text-decoration: none;">🗑️</a>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- Sidebar Info -->
            <div class="media-sidebar">
                <div class="stat-badge-box">
                    <h3>Progresso de Leitura 📖</h3>
                    <div class="stat-number">
                        {% set lidos = dados.livros | selectattr('concluido', 'equalto', True) | list | length %}
                        {{ lidos }} / {{ dados.meta_livros_quero }}
                    </div>
                    <p style="margin: 0; font-size: 0.85rem; color: var(--text-muted);">livros devorados este ano!</p>
                    <form action="/update_goal/livros" method="POST" style="margin-top: 10px; display: flex; gap: 5px; justify-content: center;">
                        <input type="number" name="goal" value="{{ dados.meta_livros_quero }}" style="width: 50px; text-align: center; border-radius: 4px; border: 1px solid var(--border-color);">
                        <button type="submit" style="font-size: 0.75rem; border: none; background: var(--accent-terracotta); color: white; padding: 2px 8px; border-radius: 4px; cursor: pointer;">Mudar Meta</button>
                    </form>
                </div>

                <div class="stat-badge-box" style="background: linear-gradient(135deg, #EADEC9 0%, #FAF6F0 100%);">
                    <h3>Cinema & Pipoca 🍿</h3>
                    <div class="stat-number">
                        {% set assistidos = dados.filmes | selectattr('concluido', 'equalto', True) | list | length %}
                        {{ assistidos }} / {{ dados.meta_filmes_quero }}
                    </div>
                    <p style="margin: 0; font-size: 0.85rem; color: var(--text-muted);">filmes assistidos!</p>
                    <form action="/update_goal/filmes" method="POST" style="margin-top: 10px; display: flex; gap: 5px; justify-content: center;">
                        <input type="number" name="goal" value="{{ dados.meta_filmes_quero }}" style="width: 50px; text-align: center; border-radius: 4px; border: 1px solid var(--border-color);">
                        <button type="submit" style="font-size: 0.75rem; border: none; background: var(--accent-terracotta); color: white; padding: 2px 8px; border-radius: 4px; cursor: pointer;">Mudar Meta</button>
                    </form>
                </div>

                <div class="top5-box">
                    <h3>⭐ Top 5 Favoritos</h3>
                    <ol class="top5-list">
                        {% set favoritos = [] %}
                        {% for l in dados.livros if l.nota == '5' %}
                            {% set _ = favoritos.append("📖 " ~ l.titulo) %}
                        {% endfor %}
                        {% for f in dados.filmes if f.nota == '5' %}
                            {% set _ = favoritos.append("🎬 " ~ f.titulo) %}
                        {% endfor %}
                        
                        {% if favoritos|length == 0 %}
                            <p style="font-size: 0.85rem; font-style: italic; color: var(--text-muted); padding: 0; margin: 0;">Dê nota de 5 estrelas para as suas mídias favoritas!</p>
                        {% else %}
                            {% for fav in favoritos[:5] %}
                                <li>{{ fav }}</li>
                            {% endfor %}
                        {% endif %}
                    </ol>
                </div>

                <div class="top5-box" style="background-color: #FFFDF9; border: 1px dashed var(--accent-terracotta);">
                    <h3>📝 Insights & Reflexões</h3>
                    <form action="/save_notes" method="POST">
                        <textarea class="notes-textarea" name="anotacoes" placeholder="Escreva passagens marcantes...">{{ dados.anotacoes_midia }}</textarea>
                        <button type="submit" class="btn-save-notes">Salvar Notas</button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- ABA 4: CONTROLE FINANCEIRO -->
    <div id="tab-financeiro" class="tab-content">
        <div class="fin-layout">
            <div>
                <!-- ENTRADAS -->
                <div class="fin-column">
                    <h2 class="fin-title">📥 Entrada (Salário Líquido, Benefícios...)</h2>
                    <form action="/add_financeiro/entradas" method="POST" class="fin-form">
                        <input type="text" name="desc" placeholder="Ex: Salário, VR, Reembolso..." required>
                        <input type="number" step="0.01" name="valor" placeholder="R$ 0,00" required>
                        <button type="submit">+</button>
                    </form>
                    <div class="fin-list">
                        {% for item in dados.entradas %}
                        <div class="fin-item">
                            <span>{{ item.desc }}</span>
                            <span style="color: var(--accent-green); font-weight: bold;">R$ {{ "%.2f"|format(item.valor) }} <a href="/delete_financeiro/entradas/{{ loop.index0 }}" style="text-decoration:none; margin-left: 8px;">🗑️</a></span>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <!-- GASTOS FIXOS -->
                <div class="fin-column">
                    <h2 class="fin-title">🏠 Gastos Fixos (Contas recorrentes)</h2>
                    <form action="/add_financeiro/gastos_fixos" method="POST" class="fin-form">
                        <input type="text" name="desc" placeholder="Ex: Luz, Internet, Aluguel..." required>
                        <input type="number" step="0.01" name="valor" placeholder="R$ 0,00" required>
                        <button type="submit">+</button>
                    </form>
                    <div class="fin-list">
                        {% for item in dados.gastos_fixos %}
                        <div class="fin-item">
                            <span>{{ item.desc }}</span>
                            <span style="color: var(--text-main);">R$ {{ "%.2f"|format(item.valor) }} <a href="/delete_financeiro/gastos_fixos/{{ loop.index0 }}" style="text-decoration:none; margin-left: 8px;">🗑️</a></span>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <!-- GASTOS VARIÁVEIS -->
                <div class="fin-column">
                    <h2 class="fin-title">🛒 Gastos Variáveis (Cartão, Uber, Lazer...)</h2>
                    <form action="/add_financeiro/gastos_variaveis" method="POST" class="fin-form">
                        <input type="text" name="desc" placeholder="Ex: Mercado, Farmácia, Saídas..." required>
                        <input type="number" step="0.01" name="valor" placeholder="R$ 0,00" required>
                        <button type="submit">+</button>
                    </form>
                    <div class="fin-list">
                        {% for item in dados.gastos_variaveis %}
                        <div class="fin-item">
                            <span>{{ item.desc }}</span>
                            <span style="color: var(--text-main);">R$ {{ "%.2f"|format(item.valor) }} <a href="/delete_financeiro/gastos_variaveis/{{ loop.index0 }}" style="text-decoration:none; margin-left: 8px;">🗑️</a></span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- Resumos e Filtro de Compras -->
            <div class="media-sidebar">
                <div class="resumo-box">
                    <h3 class="resumo-title">📊 Resumo Mensal</h3>
                    <div class="resumo-row">
                        <span>Saldo Inicial (Mês Anterior):</span>
                        <form action="/update_saldo_inicial" method="POST" style="display:flex; gap:5px;">
                            <input type="number" step="0.01" name="saldo" value="{{ dados.saldo_inicial }}" style="width:70px; border-radius:4px; border:1px solid var(--border-color); text-align:center;">
                            <button type="submit" style="font-size:0.7rem; background: var(--accent-terracotta); border:none; color:white; padding:2px 5px; border-radius:4px; cursor:pointer;">ok</button>
                        </form>
                    </div>

                    {% set total_entradas = dados.entradas | map(attribute='valor') | sum %}
                    {% set total_fixos = dados.gastos_fixos | map(attribute='valor') | sum %}
                    {% set total_variaveis = dados.gastos_variaveis | map(attribute='valor') | sum %}
                    {% set saldo_final = dados.saldo_inicial + total_entradas - (total_fixos + total_variaveis) %}

                    <div class="resumo-row">
                        <span>Total de Entradas (+):</span>
                        <span style="color: var(--accent-green);">R$ {{ "%.2f"|format(total_entradas) }}</span>
                    </div>
                    <div class="resumo-row">
                        <span>Gastos Fixos (-):</span>
                        <span style="color: var(--accent-red);">R$ {{ "%.2f"|format(total_fixos) }}</span>
                    </div>
                    <div class="resumo-row">
                        <span>Gastos Variáveis (-):</span>
                        <span style="color: var(--accent-red);">R$ {{ "%.2f"|format(total_variaveis) }}</span>
                    </div>

                    {% if saldo_final >= 0 %}
                    <div class="saldo-final-box saldo-positivo">
                        Sobra no Final do Mês: <br>
                        <strong>R$ {{ "%.2f"|format(saldo_final) }} 🎉</strong>
                    </div>
                    {% else %}
                    <div class="saldo-final-box saldo-negativo">
                        Falta no Final do Mês: <br>
                        <strong>R$ {{ "%.2f"|format(saldo_final) }} ⚠️</strong>
                    </div>
                    {% endif %}
                </div>

                <div class="filtro-impulso">
                    <div class="filtro-box" style="border-color: var(--accent-peach);">
                        <h3 style="color: var(--accent-terracotta);">🛍️ Quero (Desejo)</h3>
                        <form action="/add_impulso/quero" method="POST">
                            <input type="text" name="item" placeholder="Blusinha, gadget..." required>
                            <button type="submit">+</button>
                        </form>
                        <ul style="padding-left:15px; margin:0; font-size:0.85rem;">
                            {% for item in dados.quero %}
                            <li style="margin-bottom:5px;">
                                {{ item }} <a href="/delete_impulso/quero/{{ loop.index0 }}" style="text-decoration:none;">🗑️</a>
                            </li>
                            {% endfor %}
                        </ul>
                    </div>

                    <div class="filtro-box" style="border-color: var(--accent-green);">
                        <h3 style="color: var(--accent-green);">📍 Preciso (Necessidade)</h3>
                        <form action="/add_impulso/preciso" method="POST">
                            <input type="text" name="item" placeholder="Lente óculos, conserto..." required>
                            <button type="submit">+</button>
                        </form>
                        <ul style="padding-left:15px; margin:0; font-size:0.85rem;">
                            {% for item in dados.preciso %}
                            <li style="margin-bottom:5px;">
                                {{ item }} <a href="/delete_impulso/preciso/{{ loop.index0 }}" style="text-decoration:none;">🗑️</a>
                            </li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(function(content) {
                content.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(function(btn) {
                btn.classList.remove('active');
            });

            document.getElementById('tab-' + tabName).classList.add('active');
            document.getElementById('btn-' + tabName).classList.add('active');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    dados = ler_dados()
    return render_template_string(HTML_TEMPLATE, dados=dados)

@app.route('/add', methods=['POST'])
def add_task():
    task_text = request.form.get('task_text')
    if task_text:
        dados = ler_dados()
        dados['brain_dump'].append(task_text)
        salvar_dados(dados)
    return redirect(url_for('index'))

@app.route('/move/<origem>/<destino>/<int:index>')
def move_task(origem, destino, index):
    dados = ler_dados()
    try:
        task = dados[origem].pop(index)
        dados[destino].append(task)
        salvar_dados(dados)
    except IndexError:
        pass
    return redirect(url_for('index'))

@app.route('/delete/<coluna>/<int:index>')
def delete_task(coluna, index):
    dados = ler_dados()
    try:
        dados[coluna].pop(index)
        salvar_dados(dados)
    except IndexError:
        pass
    return redirect(url_for('index'))

@app.route('/add_smart', methods=['POST'])
def add_smart():
    dados = ler_dados()
    nova_meta = {
        "goal_name": request.form.get("goal_name"),
        "step1_desc": request.form.get("step1_desc"),
        "step1_time": request.form.get("step1_time"),
        "step1_deadline": request.form.get("step1_deadline"),
        "step2_desc": request.form.get("step2_desc"),
        "step2_time": request.form.get("step2_time"),
        "step2_deadline": request.form.get("step2_deadline"),
        "resources": request.form.get("resources"),
        "obstacles": request.form.get("obstacles"),
        "plan_obstacles": request.form.get("plan_obstacles"),
        "success_measurement": request.form.get("success_measurement"),
        "achieved_outcome": request.form.get("achieved_outcome")
    }
    dados['metas_smart'].append(nova_meta)
    salvar_dados(dados)
    return redirect(url_for('index'))

@app.route('/delete_smart/<int:index>')
def delete_smart(index):
    dados = ler_dados()
    try:
        dados['metas_smart'].pop(index)
        salvar_dados(dados)
    except IndexError:
        pass
    return redirect(url_for('index'))

@app.route('/add_media/<tipo>', methods=['POST'])
def add_media(tipo):
    dados = ler_dados()
    nova_midia = {
        "titulo": request.form.get("titulo"),
        "autor": request.form.get("autor"),
        "nota": request.form.get("nota"),
        "concluido": False
    }
    if tipo in ['livros', 'filmes']:
        dados[tipo].append(nova_midia)
        salvar_dados(dados)
    return redirect(url_for('index'))

@app.route('/toggle_media/<tipo>/<int:index>')
def toggle_media(tipo, index):
    dados = ler_dados()
    try:
        dados[tipo][index]["concluido"] = not dados[tipo][index]["concluido"]
        salvar_dados(dados)
    except (IndexError, KeyError):
        pass
    return redirect(url_for('index'))

@app.route('/delete_media/<tipo>/<int:index>')
def delete_media(tipo, index):
    dados = ler_dados()
    try:
        dados[tipo].pop(index)
        salvar_dados(dados)
    except (IndexError, KeyError):
        pass
    return redirect(url_for('index'))

@app.route('/update_goal/<tipo>', methods=['POST'])
def update_goal(tipo):
    dados = ler_dados()
    meta_val = request.form.get("goal")
    if meta_val:
        if tipo == 'livros':
            dados["meta_livros_quero"] = int(meta_val)
        elif tipo == 'filmes':
            dados["meta_filmes_quero"] = int(meta_val)
        salvar_dados(dados)
    return redirect(url_for('index'))

@app.route('/save_notes', methods=['POST'])
def save_notes():
    dados = ler_dados()
    dados["anotacoes_midia"] = request.form.get("anotacoes")
    salvar_dados(dados)
    return redirect(url_for('index'))

# --- ROTAS FINANCEIRAS ---

@app.route('/add_financeiro/<tipo>', methods=['POST'])
def add_financeiro(tipo):
    dados = ler_dados()
    desc = request.form.get("desc")
    valor = request.form.get("valor")
    if desc and valor and tipo in ['entradas', 'gastos_fixos', 'gastos_variaveis']:
        dados[tipo].append({
            "desc": desc,
            "valor": float(valor)
        })
        salvar_dados(dados)
    return redirect(url_for('index'))

@app.route('/delete_financeiro/<tipo>/<int:index>')
def delete_financeiro(tipo, index):
    dados = ler_dados()
    try:
        dados[tipo].pop(index)
        salvar_dados(dados)
    except (IndexError, KeyError):
        pass
    return redirect(url_for('index'))

@app.route('/update_saldo_inicial', methods=['POST'])
def update_saldo_inicial():
    dados = ler_dados()
    saldo = request.form.get("saldo")
    if saldo:
        dados["saldo_inicial"] = float(saldo)
        salvar_dados(dados)
    return redirect(url_for('index'))

@app.route('/add_impulso/<tipo>', methods=['POST'])
def add_impulso(tipo):
    dados = ler_dados()
    item = request.form.get("item")
    if item and tipo in ['quero', 'preciso']:
        dados[tipo].append(item)
        salvar_dados(dados)
    return redirect(url_for('index'))

@app.route('/delete_impulso/<tipo>/<int:index>')
def delete_impulso(tipo, index):
    dados = ler_dados()
    try:
        dados[tipo].pop(index)
        salvar_dados(dados)
    except (IndexError, KeyError):
        pass
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)