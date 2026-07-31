from django.shortcuts import render, redirect
from django.contrib import messages
from backendpetmee.supabase_client import supabase

# Suas views de cadastro e login vêm aqui abaixo...


def cadastro_user(request):
    if request.method == 'POST':
        print('==== DADOS RECEBIDOS ====')
        print(request.POST)
        print('==========================')

        
        email =  request.POST.get('email', '').strip()
        senha = request.POST.get('password', '').strip()
        nome = request.POST.get('nome', '').strip()

        print('=======^^======')
        print(f'Nome:{nome}')
        print(f'Email:{email}')
        print(f'password:{senha}')
        print('================')

        try:
            # 1 Criar usuario no Supabase Auth
            response = supabase.auth.sign_up(
                credentials={
                    'email': email,
                    'password': senha,
                    'options':{
                        'data':{
                            'nome':nome,
                        }
                    }
                }
            
            )
            print('Response do Supabase:', response)
            

            if response.user:
                messages.success(request, "Cadastro realizado! Verifique seu e-mail para confirmar a conta")
                return redirect('Login.html')

        except Exception as e:
            print('ERRO SUPABASE', e)
            #erros comuns como e-mail ja cadastrado e outros.
            messages.error(request, f"Erro ao cadastrar: {str(e)}")

    return render(request, 'registro/registro.html')
                
