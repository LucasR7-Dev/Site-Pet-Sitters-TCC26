from uuid import UUID

from django.contrib import messages
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from backendpetmee.supabase_client import get_supabase


def _user_id(request):
    value = request.session.get('user_id')
    try:
        return str(UUID(str(value))) if value else None
    except (TypeError, ValueError):
        return None


def _client(request):
    """Cliente por requisição: evita compartilhar a sessão de um usuário entre usuários."""
    client = get_supabase()
    access_token = request.session.get('supabase_access_token')
    refresh_token = request.session.get('supabase_refresh_token')
    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception:
            pass
    return client


def _select_one(request, table, column, value):
    response = _client(request).table(table).select('*').eq(column, value).limit(1).execute()
    return response.data[0] if response.data else None


def _ensure_profile(request, user_id):
    """Cria o perfil para contas existentes antes da nova tabela de perfis."""
    try:
        perfil = _select_one(request, 'usuarios', 'id', user_id)
    except Exception:
        # A tela inicial continua utilizável mesmo em uma falha transitória do REST.
        return None
    if perfil:
        return perfil
    try:
        user = _client(request).auth.get_user().user
        metadata = user.user_metadata or {}
        nome = metadata.get('nome_completo') or user.email.split('@')[0]
        _client(request).table('usuarios').insert({
            'id': user_id,
            'nome_completo': nome,
            'tipo_usuario': metadata.get('tipo_usuario', 'tutor'),
            'is_cuidador': False,
        }).execute()
        return _select_one(request, 'usuarios', 'id', user_id)
    except Exception:
        return None


def cadastro_user(request):
    if request.method == 'POST':
        nome_completo = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('password', '')
        if not nome_completo or not email or not senha:
            messages.error(request, 'Preencha todos os campos.')
            return render(request, 'registro/registro.html')
        try:
            resposta = get_supabase().auth.sign_up({
                'email': email, 'password': senha,
                'options': {'data': {
                    'nome_completo': nome_completo,
                    'tipo_usuario': 'tutor',
                }},
            })
            if not resposta.user:
                raise ValueError('Usuário não retornado pelo Supabase.')
            # Em projetos com confirmação de e-mail, o usuário ainda não tem sessão
            # autenticada aqui. O trigger do schema cria o perfil nesse caso.
            try:
                get_supabase().table('usuarios').upsert({
                    'id': str(resposta.user.id),
                    'nome_completo': nome_completo,
                    'tipo_usuario': 'tutor',
                    'is_cuidador': False,
                }).execute()
            except Exception:
                pass
            messages.success(request, 'Cadastro realizado. Faça seu login.')
            return redirect('login')
        except Exception:
            messages.error(request, 'Não foi possível concluir o cadastro. Tente novamente.')
    return render(request, 'registro/registro.html')


def login_user(request):
    if request.method == 'POST':
        try:
            resposta = get_supabase().auth.sign_in_with_password({
                'email': request.POST.get('email', '').strip(),
                'password': request.POST.get('password', ''),
            })
            if resposta.user:
                request.session['user_id'] = str(resposta.user.id)
                request.session['supabase_access_token'] = resposta.session.access_token
                request.session['supabase_refresh_token'] = resposta.session.refresh_token
                return redirect('home')
        except Exception:
            pass
        messages.error(request, 'E-mail ou senha inválidos.')
        return redirect('login')
    return render(request, 'Login/Login.html')


def home(request):
    user_id = _user_id(request)
    if not user_id:
        return redirect('login')
    _ensure_profile(request, user_id)
    try:
        client = _client(request)
        pets = client.table('pets').select('*').eq('disponivel', True).order('created_at', desc=True).execute().data
        cuidadores = client.table('usuarios').select('*').eq(
            'is_cuidador', True
        ).order('created_at', desc=True).limit(6).execute().data
    except Exception:
        pets, cuidadores = [], []
    return render(request, 'home/inicio.html', {'pets': pets, 'cuidadores': cuidadores})


def sobre(request):
    return render(request, 'Sobre.html')


def tornar_cuidador(request):
    user_id = _user_id(request)
    if not user_id:
        return redirect('login')
    perfil = _select_one(request, 'usuarios', 'id', user_id) or {}
    if request.method == 'POST':
        genero = request.POST.get('genero', '').strip().lower()
        estado = request.POST.get('estado', '').strip().upper()
        cidade = request.POST.get('cidade', '').strip()
        bio = request.POST.get('bio', '').strip()
        idade = request.POST.get('idade', '').strip()
        if genero not in {'masculino', 'feminino'} or not estado or not cidade or not idade:
            messages.error(request, 'Informe gênero, idade, estado e cidade para se tornar cuidador.')
        else:
            values = {
                'is_cuidador': True,
                'genero': genero,
                'estado': estado,
                'cidade': cidade,
                'bio': bio,
            }
            if idade:
                try:
                    values['idade'] = int(idade)
                    if not 21 <= values['idade'] <= 60:
                        raise ValueError
                except ValueError:
                    messages.error(request, 'Para ser cuidador, a idade precisa estar entre 21 e 60 anos.')
                    return render(request, 'cuidador/formulario.html', {'perfil': perfil})
            try:
                _client(request).table('usuarios').update(values).eq('id', user_id).execute()
                messages.success(request, 'Seu perfil agora está disponível para quem procura cuidadores.')
                return redirect('search_cuidadores')
            except Exception:
                messages.error(request, 'Não foi possível salvar o cadastro de cuidador. Confira o SQL do Supabase.')
    return render(request, 'cuidador/formulario.html', {'perfil': perfil})


def _ratings_by_user(request):
    ratings = _client(request).table('avaliacoes').select('avaliado_id, nota').execute().data
    grouped = {}
    for rating in ratings:
        user_id = str(rating.get('avaliado_id'))
        grouped.setdefault(user_id, []).append(float(rating.get('nota', 0)))
    return {
        user_id: round(sum(values) / len(values), 1)
        for user_id, values in grouped.items()
        if values
    }


def search_cuidadores(request):
    filters = {
        'estado': request.GET.get('estado', '').strip().upper(),
        'cidade': request.GET.get('cidade', '').strip(),
        'genero': request.GET.get('genero', '').strip().lower(),
        'estrelas': request.GET.get('estrelas', '').strip(),
        'idade_min': request.GET.get('idade_min', '').strip(),
        'idade_max': request.GET.get('idade_max', '').strip(),
    }
    try:
        idade_min = int(filters['idade_min']) if filters['idade_min'] else 21
        idade_max = int(filters['idade_max']) if filters['idade_max'] else 60
        idade_min = max(21, min(60, idade_min))
        idade_max = max(21, min(60, idade_max))
        if idade_min > idade_max:
            idade_min, idade_max = idade_max, idade_min
    except (TypeError, ValueError):
        idade_min, idade_max = 21, 60
    filters['idade_min'], filters['idade_max'] = str(idade_min), str(idade_max)
    cuidadores = []
    try:
        query = _client(request).table('usuarios').select('*').eq('is_cuidador', True)
        if filters['estado']:
            query = query.eq('estado', filters['estado'])
        if filters['cidade']:
            query = query.eq('cidade', filters['cidade'])
        if filters['genero'] in {'masculino', 'feminino'}:
            query = query.eq('genero', filters['genero'])
        query = query.gte('idade', idade_min).lte('idade', idade_max)
        ratings = _ratings_by_user(request)
        minimum_rating = float(filters['estrelas']) if filters['estrelas'] else 0
        for cuidador in query.order('created_at', desc=True).execute().data:
            cuidador['media_avaliacoes'] = ratings.get(str(cuidador.get('id')), 0)
            if cuidador['media_avaliacoes'] >= minimum_rating:
                cuidadores.append(cuidador)
    except Exception:
        cuidadores = []
    return render(request, 'search_cuidadores.html', {
        'cuidadores': cuidadores,
        'filters': filters,
    })


def petshops(request):
    """Lista petshops e coloca os que estão na região do usuário primeiro."""
    petshops_list = []
    user_location = {}
    user_id = _user_id(request)
    try:
        if user_id:
            user_location = _select_one(request, 'usuarios', 'id', user_id) or {}
        registros = _client(request).table('usuarios').select('*').eq(
            'tipo_usuario', 'petshop'
        ).order('created_at', desc=True).execute().data
        user_city = (user_location.get('cidade') or '').casefold()
        user_state = (user_location.get('estado') or '').upper()
        for petshop in registros:
            shop_city = (petshop.get('cidade') or '').casefold()
            shop_state = (petshop.get('estado') or '').upper()
            if user_city and shop_city == user_city and user_state and shop_state == user_state:
                petshop['proximidade'] = 'Na sua cidade'
                petshop['_distance_rank'] = 0
            elif user_state and shop_state == user_state:
                petshop['proximidade'] = 'No seu estado'
                petshop['_distance_rank'] = 1
            else:
                petshop['proximidade'] = 'Petshop parceiro'
                petshop['_distance_rank'] = 2
            petshop['cidade_display'] = petshop.get('cidade') or 'Região não informada'
            petshop['estado_display'] = petshop.get('estado') or ''
            petshops_list.append(petshop)
        petshops_list.sort(key=lambda item: (item['_distance_rank'], item.get('nome_completo', '').casefold()))
    except Exception:
        petshops_list = []
    return render(request, 'petshops/petshops.html', {
        'petshops': petshops_list,
        'user_location': user_location,
    })


def loja(request):
    filters = {
        'busca': request.GET.get('busca', '').strip(),
        'categoria': request.GET.get('categoria', '').strip(),
        'min_preco': request.GET.get('min_preco', '').strip(),
        'max_preco': request.GET.get('max_preco', '').strip(),
    }
    produtos = []
    categorias = []
    try:
        registros = _client(request).table('produtos').select('*').eq('ativo', True).order(
            'created_at', desc=True
        ).execute().data
        ids = {str(produto.get('vendedor_id')) for produto in registros}
        vendedores = {}
        for user_id in ids:
            perfil = _select_one(request, 'usuarios', 'id', user_id)
            if perfil:
                vendedores[user_id] = perfil.get('nome_completo', 'Petshop')
        for produto in registros:
            categoria = produto.get('categoria') or 'Geral'
            categorias.append(categoria)
            nome = (produto.get('nome') or '').lower()
            matches_search = not filters['busca'] or filters['busca'].lower() in nome
            matches_category = not filters['categoria'] or filters['categoria'] == categoria
            try:
                preco = float(produto.get('preco', 0))
            except (TypeError, ValueError):
                preco = 0
            matches_min = not filters['min_preco'] or preco >= float(filters['min_preco'])
            matches_max = not filters['max_preco'] or preco <= float(filters['max_preco'])
            if matches_search and matches_category and matches_min and matches_max:
                produto['vendedor_nome'] = vendedores.get(str(produto.get('vendedor_id')), 'Petshop')
                produtos.append(produto)
    except (Exception, ValueError):
        produtos = []
    return render(request, 'loja/loja.html', {
        'produtos': produtos,
        'categorias': sorted(set(categorias)),
        'filters': filters,
    })


def cadastrar_produto(request):
    user_id = _user_id(request)
    if not user_id:
        return redirect('login')
    perfil = _select_one(request, 'usuarios', 'id', user_id) or {}
    if perfil.get('tipo_usuario') != 'petshop':
        messages.error(request, 'Apenas contas do tipo Petshop podem cadastrar produtos.')
        return redirect('loja')
    if request.method == 'POST':
        produto = {
            'vendedor_id': user_id,
            'nome': request.POST.get('nome', '').strip(),
            'descricao': request.POST.get('descricao', '').strip(),
            'categoria': request.POST.get('categoria', '').strip(),
            'foto_url': request.POST.get('foto_url', '').strip(),
            'ativo': True,
        }
        try:
            produto['preco'] = float(request.POST.get('preco', '0').replace(',', '.'))
            produto['estoque'] = int(request.POST.get('estoque', '0'))
            if not produto['nome'] or produto['preco'] < 0 or produto['estoque'] < 0:
                raise ValueError
            _client(request).table('produtos').insert(produto).execute()
            messages.success(request, 'Produto publicado na loja.')
            return redirect('loja')
        except (ValueError, TypeError):
            messages.error(request, 'Informe nome, preço e estoque com valores válidos.')
        except Exception:
            messages.error(request, 'Não foi possível publicar o produto. Confira o SQL do Supabase.')
    return render(request, 'loja/produto_form.html', {'perfil': perfil})


def cadastrar_pet(request):
    owner_id = _user_id(request)
    if not owner_id:
        return redirect('login')
    if request.method == 'POST':
        fields = ('nome', 'especie', 'raca', 'sexo', 'porte', 'idade', 'localizacao', 'saude', 'sobre', 'foto_url')
        pet = {field: request.POST.get(field, '').strip() for field in fields}
        if not pet['nome'] or not pet['especie'] or not pet['localizacao']:
            messages.error(request, 'Nome, espécie e localização são obrigatórios.')
        else:
            pet.update({'tutor_id': owner_id, 'disponivel': True})
            try:
                novo_pet = _client(request).table('pets').insert(pet).execute().data[0]
                messages.success(request, 'Pet cadastrado com sucesso.')
                return redirect('detalhes_pet', pet_id=novo_pet['id'])
            except Exception:
                messages.error(request, 'Não foi possível salvar o pet. Confira o SQL do Supabase.')
    return render(request, 'pets/formulario.html')


def detalhes_pet(request, pet_id):
    try:
        pet = _select_one(request, 'pets', 'id', pet_id)
    except Exception as exc:
        raise Http404('Pet não encontrado.') from exc
    if not pet:
        raise Http404('Pet não encontrado.')
    return render(request, 'perfil/perfil1.html', {
        'pet': pet, 'is_owner': _user_id(request) == str(pet.get('tutor_id')),
    })


def meu_perfil(request):
    user_id = _user_id(request)
    return redirect('login') if not user_id else redirect('perfil_usuario', user_id=user_id)


def perfil_usuario(request, user_id):
    try:
        perfil = _select_one(request, 'usuarios', 'id', str(user_id))
        if not perfil and _user_id(request) == str(user_id):
            perfil = _ensure_profile(request, str(user_id))
        avaliacoes = _client(request).table('avaliacoes').select('*').eq('avaliado_id', str(user_id)).order('created_at', desc=True).execute().data
    except Exception:
        perfil, avaliacoes = None, []
    if not perfil:
        raise Http404('Perfil não encontrado.')
    media = round(sum(item['nota'] for item in avaliacoes) / len(avaliacoes), 1) if avaliacoes else None
    return render(request, 'perfil/perfil.html', {
        'perfil': perfil, 'avaliacoes': avaliacoes, 'media_avaliacoes': media,
        'is_owner': _user_id(request) == str(user_id),
    })


def editar_perfil(request, user_id):
    if _user_id(request) != str(user_id):
        return HttpResponseForbidden('Você só pode editar o seu próprio perfil.')
    if request.method == 'POST':
        values = {key: request.POST.get(key, '').strip() for key in ('nome_completo', 'cidade', 'estado', 'idade', 'bio', 'avatar_url')}
        try:
            _client(request).table('usuarios').update(values).eq('id', str(user_id)).execute()
            messages.success(request, 'Perfil atualizado.')
            return redirect('perfil_usuario', user_id=user_id)
        except Exception:
            messages.error(request, 'Não foi possível atualizar o perfil.')
    return render(request, 'perfil/editar.html', {'perfil': _select_one(request, 'usuarios', 'id', str(user_id))})


def criar_avaliacao(request, user_id):
    autor_id = _user_id(request)
    if not autor_id:
        return redirect('login')
    if autor_id == str(user_id):
        messages.error(request, 'Você não pode avaliar o próprio perfil.')
    elif request.method == 'POST':
        try:
            nota = int(request.POST.get('nota', 0))
            comentario = request.POST.get('comentario', '').strip()
            if nota not in range(1, 6) or not comentario:
                raise ValueError
            _client(request).table('avaliacoes').upsert({
                'autor_id': autor_id, 'avaliado_id': str(user_id), 'nota': nota, 'comentario': comentario,
            }, on_conflict='autor_id,avaliado_id').execute()
            messages.success(request, 'Sua avaliação foi publicada.')
        except ValueError:
            messages.error(request, 'Informe uma nota de 1 a 5 e escreva um comentário.')
        except Exception:
            messages.error(request, 'Não foi possível publicar sua avaliação.')
    return redirect('perfil_usuario', user_id=user_id)
