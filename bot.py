from typing import Final
import ast
from tabulate import tabulate
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pandas as pd
import pygsheets

TOKEN : Final = '7114531591:AAE9K7-80Gx-_sr_cfR1GuVupnAW5AFOO5o'
BOT_USERNAME : Final = '@MBE_Visagio_Bot'
PLACAR : Final = pd.DataFrame({'Dupla':[], 'Integrantes': [], 'Placar': [], 'ValorDiario': [], 'Meetup': [], 'Vibe': [], 'AtivFisica': [], 'AtivRelax': [], 'Atividade1': []})
GC : Final = pygsheets.authorize(service_file='credentials.json')
SH : Final = GC.open('MBE')
WKS : Final = SH[0]
ADMIN : Final = 6837505886

# Commands
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN
    if update.message.from_user.id == ADMIN:
        reset()
        await update.message.reply_text('Tabela resetada com sucesso')

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN
    if update.message.from_user.id == ADMIN:
        update_placar(context.args[0], context.args[1], context.args[2])
        await update.message.reply_text('Placar atualizado com sucesso')

async def write_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global WKS
    global PLACAR
    global ADMIN
    if update.message.from_user.id == ADMIN:
        WKS.clear()
        WKS.set_dataframe(PLACAR,(1,1))
        await update.message.reply_text('Google sheets atualizado com sucesso')

async def read_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global WKS
    global PLACAR
    global ADMIN
    if update.message.from_user.id == ADMIN:
        PLACAR = WKS.get_as_df()
        PLACAR.ValorDiario = PLACAR.ValorDiario.astype(int)
        PLACAR.Placar = PLACAR.Placar.astype(int)
        PLACAR.AtivFisica = PLACAR.AtivFisica.astype(int)
        PLACAR.AtivRelax = PLACAR.AtivRelax.astype(int)
        PLACAR.Integrantes = PLACAR.Integrantes.apply(mySetConv)
        PLACAR.Meetup = PLACAR.Meetup.map({'TRUE': True, 'FALSE': False, 0: False, 1: True})
        PLACAR.Vibe = PLACAR.Vibe.map({'TRUE': True, 'FALSE': False, 0: False, 1: True})
        PLACAR.Atividade1 = PLACAR.Atividade1.map({'TRUE': True, 'FALSE': False, 0: False, 1: True})
        await update.message.reply_text('PLACAR atualizado com sucesso')

# Handle Responses
def reset():
    global PLACAR
    global WKS
    PLACAR['ValorDiario'] = 0
    PLACAR['Meetup'] = False
    PLACAR['Vibe'] = False
    PLACAR['AtivFisica'] = 0
    PLACAR['AtivRelax'] = 0
    PLACAR['Atividade1'] = False
    PLACAR.ValorDiario = PLACAR.ValorDiario.astype(int)
    PLACAR.Placar = PLACAR.Placar.astype(int)
    PLACAR.AtivFisica = PLACAR.AtivFisica.astype('int64')
    PLACAR.AtivRelax = PLACAR.AtivRelax.astype('int64')
    WKS.clear()
    WKS.set_dataframe(PLACAR,(1,1))
    return 'Tabela Resetada com Sucesso'
    
def update_placar(nomeDupla, valor, coluna):
    global PLACAR
    idx = PLACAR.Dupla.explode().eq(nomeDupla).loc[lambda x: x].index.values[0]
    PLACAR.at[idx, coluna] = valor

def mySetConv(txt):
    return dict() if txt == '{}' else ast.literal_eval(txt)

def pontuar(idPessoal, pontos, typ):
    global PLACAR
    global WKS
    idx = PLACAR.Integrantes.explode().eq(idPessoal).loc[lambda x: x].index
    al = PLACAR.loc[idx]
    if al.empty:
        return f'Usuário não registrado em nenhuma dupla'
    al = al.iloc[0]
    if PLACAR.at[idx.values[0], "ValorDiario"] == 6:
        return f'Parabéns, a pontuação máxima diária de 6 pontos já foi atingida pela dupla "{PLACAR.at[idx.values[0], "Dupla"]}"! Faça mais atividades amanhã para garantir ainda mais pontos.'
    mini = min(6 - int(PLACAR.at[idx.values[0], "ValorDiario"]), pontos)
    if typ == 'Meetup':
        if al['Meetup'] == True:
            return f'Atividade Meetup já foi registrada anteriormente para a dupla "{al["Dupla"]}"'
        PLACAR.at[idx.values[0], "Meetup"] = True
        PLACAR.at[idx.values[0], "Placar"] += mini
        PLACAR.at[idx.values[0], "ValorDiario"] += mini
        WKS.clear()
        WKS.set_dataframe(PLACAR,(1,1))
    elif typ == 'Vibe':   
        if al['Vibe'] == True:
            return f'Atividade Vibe já foi registrada anteriormente para a dupla "{al["Dupla"]}"'
        PLACAR.at[idx.values[0], "Vibe"] = True
        PLACAR.at[idx.values[0], "Placar"] += mini
        PLACAR.at[idx.values[0], "ValorDiario"] += mini
        WKS.clear()
        WKS.set_dataframe(PLACAR,(1,1))
    elif typ == 'Atividade1':   
        if al['Atividade1'] == True:
            return f'A atividade1 já foi registrada anteriormente para a dupla "{al["Dupla"]}"'
        PLACAR.at[idx.values[0], "Atividade1"] = True
        PLACAR.at[idx.values[0], "Placar"] += mini
        PLACAR.at[idx.values[0], "ValorDiario"] += mini
        WKS.clear()
        WKS.set_dataframe(PLACAR,(1,1))
    elif typ == 'AtivFisica':
        if al['AtivFisica'] == sum(PLACAR.at[idx.values[0], "Integrantes"].keys()):
            return f'A atividade física já foi registrada anteriormente para a dupla "{al["Dupla"]}"'
        if al['AtivFisica'] == idPessoal:
            return f'A atividade física já foi registrada por você para a dupla "{al["Dupla"]}"'
        PLACAR.at[idx.values[0], "AtivFisica"] = int(PLACAR.at[idx.values[0], "AtivFisica"]) + idPessoal
        PLACAR.at[idx.values[0], "Placar"] += mini
        PLACAR.at[idx.values[0], "ValorDiario"] += mini
        WKS.clear()
        WKS.set_dataframe(PLACAR,(1,1))
    elif typ == 'AtivRelax':
        if al['AtivRelax'] == sum(PLACAR.at[idx.values[0], "Integrantes"].keys()):
            return f'A atividade relax já foi registrada anteriormente para a dupla "{al["Dupla"]}"'
        if al['AtivRelax'] == idPessoal:
            return f'A atividade relax já foi registrada por você para a dupla "{al["Dupla"]}"'
        PLACAR.at[idx.values[0], "AtivRelax"] = int(PLACAR.at[idx.values[0], "AtivRelax"]) + idPessoal
        PLACAR.at[idx.values[0], "Placar"] += mini
        PLACAR.at[idx.values[0], "ValorDiario"] += mini
        WKS.clear()
        WKS.set_dataframe(PLACAR,(1,1))
    elif typ == 'exit':
        PLACAR.at[idx.values[0], "Placar"] += pontos
        WKS.clear()
        WKS.set_dataframe(PLACAR,(1,1))
    elif typ == 'registrar':
        PLACAR.at[idx.values[0], "Placar"] += pontos
        WKS.clear()
        WKS.set_dataframe(PLACAR,(1,1))
        return
    return f'Obrigado {PLACAR.at[idx.values[0], "Integrantes"][idPessoal]}, você marcou mais {mini} pontos, sua dupla {al["Dupla"]} agora está com {int(PLACAR.at[idx.values[0], "Placar"])} pontos'
        

def handle_response(processed: str, update: Update) -> str:
    global PLACAR
    idPessoal = int(update.message.from_user.id)
    idx = PLACAR.Integrantes.explode().eq(idPessoal).loc[lambda x: x].index
    if '/registrar' == processed:
        return 'Comando não válido. Formato de uso: "/registrar Nome.Visagio NomeDupla"'
    
    if '/registrar' in processed:
        text = processed.split('/registrar')[1].strip().split(' ')
        nomedupla = text[1]
        nomepessoa = text[0]
        if '.' not in nomepessoa:
            return f'{update.message.from_user.first_name}, verifique o seu nome Visagio. Formato de uso: "/registrar Nome.Visagio NomeDupla"'
        al = PLACAR.loc[PLACAR.Integrantes.explode().eq(idPessoal).loc[lambda x: x].index, "Dupla"]
        troca = False
        if not al.empty:
            if nomedupla == PLACAR.loc[al.index[0], 'Dupla'] or update.message.date > datetime(2024, 3, 2, 3, 0, tzinfo=timezone.utc):
                return f'Opa, {nomepessoa}. Você já está registrado na dupla "{al.iloc[0]}"'
            else:
                PLACAR.loc[al.index[0], 'Integrantes'].pop(idPessoal)
                troca = True
                if len(PLACAR.loc[al.index[0], 'Integrantes']) == 0:
                    PLACAR.drop(al.index[0], inplace=True)
        
        if nomedupla not in PLACAR.Dupla.values:
            PLACAR = pd.concat([PLACAR, pd.DataFrame({'Dupla': [nomedupla], 'Integrantes': [{idPessoal: nomepessoa}], 'Placar': [0], 'ValorDiario': [0], 'Meetup': [False], 'Vibe': [False], 'AtivFisica': [0], 'AtivRelax': [0], 'Atividade1': [False]})], axis=0, ignore_index=True)
            WKS.clear()
            WKS.set_dataframe(PLACAR,(1,1))
            if update.message.date < datetime(2024, 3, 1, 3, 0, tzinfo=timezone.utc):
                pontuar(idPessoal, 2, 'registrar')
            elif update.message.date < datetime(2024, 3, 4, 3, 0, tzinfo=timezone.utc):
                pontuar(idPessoal, 1, 'registrar')
            if troca:
                return f'Dupla trocada com sucesso, {nomepessoa}!'
            return f'Seja muito bem vindo ao grupo do mês do bem estar, {nomepessoa}'
        else:
            row = PLACAR[PLACAR['Dupla'] == nomedupla].iloc[0]
            if len(row.Integrantes) == 2:
                WKS.clear()
                WKS.set_dataframe(PLACAR,(1,1))
                return f'A dupla "{nomedupla}" já tem duas pessoas, use outro nome por favor.'
            else:
                PLACAR.loc[row.name, 'Integrantes'].add(idPessoal)
                WKS.clear()
                WKS.set_dataframe(PLACAR,(1,1))
                if update.message.date < datetime(2024, 3, 1, 3, 0, tzinfo=timezone.utc):
                    pontuar(idPessoal, 2, 'registrar')
                elif update.message.date < datetime(2024, 3, 8, 3, 0, tzinfo=timezone.utc):
                    pontuar(idPessoal, 1, 'registrar')
                return f'Seja muito bem vindo ao grupo do mês do bem estar, {nomepessoa}. Sua dupla agora está completa.'
       
    if update.message.date < datetime(2024, 3, 1, 3, 0, tzinfo=timezone.utc) and processed in ['/meetup', '/ativfisica', '/ativrelax', '/vibe']:
        return f'A atividade "{processed[1:]}" só será permitida a partir do dia 1 de março'
    if '/exit' == processed and update.message.date <= datetime(2024, 4, 1, 3, 0, tzinfo=timezone.utc) and update.message.date >= datetime(2024, 3, 31, 3, 0, tzinfo=timezone.utc):
        return pontuar(idPessoal, 1, 'exit')

    if '/atividade1' == processed:
        if update.message.date > datetime(2024, 3, 4, 3, 0, tzinfo=timezone.utc):
            return 'O prazo para envio da atividade1 foi finalizado no dia 2 de março'
        if update.message.photo == ():
            return f'{PLACAR.at[idx.values[0], "Integrantes"][idPessoal]}, para registrar atividade é obrigatório o envio de uma imagem junto com o comando.'
        return pontuar(idPessoal, 2, 'Atividade1')

    if '/placar' == processed:
        stri = "Placar atual:\n\n"
        p = PLACAR[["Dupla", "Placar"]]
        p["Placar"] = p["Placar"].astype('int')
        p.sort_values(inplace=True, by="Placar", ascending=False)
        # m = p.Dupla.astype(str).str.len().max()
        # p.Dupla = p.Dupla.astype(str).str.ljust(m, ' ')
        # p = p.to_string(index = False)
        for i, r in p.iterrows():
            print(len(str(r['Placar'])), r['Placar'])
            con = 15 - len(str(r['Placar']))
            stri += ' '*con + f"{r['Placar']} | {r['Dupla']}\n"
        return stri
    
    if '/meetup' == processed:
        if update.message.photo == ():
            return f'{PLACAR.at[idx.values[0], "Integrantes"][idPessoal]}, para registrar atividade é obrigatório o envio de uma imagem junto com o comando.'
        return pontuar(idPessoal, 4, 'Meetup')

    if '/ativfisica' == processed:
        if update.message.photo == ():
            return f'{PLACAR.at[idx.values[0], "Integrantes"][idPessoal]}, para registrar atividade é obrigatório o envio de uma imagem junto com o comando.'
        return pontuar(idPessoal, 1, 'AtivFisica')
    
    if '/ativrelax' == processed:
        if update.message.photo == ():
            return f'{PLACAR.at[idx.values[0], "Integrantes"][idPessoal]}, para registrar atividade é obrigatório o envio de uma imagem junto com o comando.'
        return pontuar(idPessoal, 1, 'AtivRelax')
    
    if '/vibe' == processed:
        if update.message.photo == ():
            return f'{PLACAR.at[idx.values[0], "Integrantes"][idPessoal]}, para registrar atividade é obrigatório o envio de uma imagem junto com o comando.'
        return pontuar(idPessoal, 4, 'Vibe')
    if '/help' == processed:
        return f'''
        Seja muito bem vindo ao grupo do mês do bem estar, {update.message.from_user.first_name}!

        -- /registrar nome.sobrenome nome dupla - você se registra na dupla desejada
        -- /placar - Traz as informações consolidadas do placar.

        Comandos para registrar pontos nas atividades, só vale com foto!

        /atividade1 : 2 pontos para a realização do pré-work até 3 de março

        A partir de 1° de março: 

            -- /ativrelax    1 ponto para atividade de descontração qualquer
            -- /ativfisica   1 ponto para exercicio fisico
            -- /meetup       4 pontos para MeetUp ViBE
            -- /vibe         4 pontos para atividade da semana do Bem Estar
        '''
    return f'''
        Oi, {update.message.from_user.first_name}!

        O comando enviado é inválido, essas são as instruções válidas:
        -- /help - comando para receber as instruções de inicio.
        -- /registrar nome.sobrenome nome_dupla - você se registra na dupla desejada
        -- /placar - Traz as informações consolidadas do placar.

        Comandos para registrar pontos nas atividades, só vale com foto!

        /atividade1 : 2 pontos para a realização do pré-work até 3 de março

        A partir de 1° de março: 

            -- /ativrelax    1 ponto para atividade de descontração qualquer
            -- /ativfisica   1 ponto para exercicio fisico
            -- /meetup       4 pontos para MeetUp ViBE
            -- /vibe         4 pontos para atividade da semana do Bem Estar'''

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    if update.message.text != None:
        text: str = update.message.text
    else:
        text: str = update.message.caption
    if text[0] == '/' and message_type == 'group':
        print(f'User {update.message.from_user.id} in {message_type}: {text}')
        response: str = handle_response(text, update)

        print('Bot: ', response)
        if response != '':
            await update.message.reply_text(response)
            if '/exit' in text:
                await update.message.chat.ban_member(user_id=update.message.from_user.id)
    

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('reset', reset_command))
    app.add_handler(CommandHandler('update', update_command))
    app.add_handler(CommandHandler('write', write_command))
    app.add_handler(CommandHandler('read', read_command))


    app.add_handler(MessageHandler(filters.ALL, handle_message))


    app.add_error_handler(error)
    print('Polling...')
    app.run_polling(poll_interval=3)