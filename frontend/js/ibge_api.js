<<<<<<< HEAD
//Api do IBGE para carregar os estados e cidades do Brasil pode ser usada para criar um filtro de busca por localização em outras paginas do site, como a página de busca de cuidadores. O código abaixo é um exemplo de como usar a API do IBGE para carregar os estados e cidades em um formulário de busca:

const selectEstado = document.getElementById('estado');
const selectCidade = document.getElementById('cidade');
//Função para carregar os Estados e abrir a pagina
async function carregarEstado(){
const response = await fetch('https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome')
const estados = await response.json();

estados.forEach(estado => {
    const option = document.createElement('option');
    option.value = estado.sigla;
    option.textContent = estado.nome;
    selectEstado.appendChild(option)
});
}
//Função para carregar acidades quando o estado mudar
selectEstado.addEventListener('change', async() =>{
    const sigla = selectEstado.value;
    selectCidade.innerHTML = '<option value="">Carregando...</option>';

    if (!sigla){
        selectCidade.innerHTML = '<option value""">Selecione o Estado primeiro</option>'
        return;
    }
    const response = await fetch(`https://servicodados.ibge.gov.br/api/v1/localidades/estados/${sigla}/municipios`)
    const cidades = await response.json();

    selectCidade.innerHTML = '<option value="">Selecione a cidade</option>';
    cidades.forEach(cidade => {
        const option = document.createElement('option');
        option.value = cidade.nome;
        option.textContent = cidade.nome;
        selectCidade.appendChild(option);
})
});
carregarEstado();
=======
const selectEstado = document.getElementById('estado');
const selectCidade = document.getElementById('cidade');
const selectedLocation = window.petmeeLocationFilters || {};

if (selectEstado && selectCidade) {
    async function carregarEstados() {
        try {
            const response = await fetch('https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome');
            const estados = await response.json();
            estados.forEach(estado => {
                const option = document.createElement('option');
                option.value = estado.sigla;
                option.textContent = estado.nome;
                option.selected = estado.sigla === selectedLocation.estado;
                selectEstado.appendChild(option);
            });
            if (selectEstado.value) await carregarCidades(selectEstado.value);
        } catch {
            selectEstado.innerHTML = '<option value="">Não foi possível carregar os estados</option>';
        }
    }

    async function carregarCidades(sigla) {
        selectCidade.disabled = !sigla;
        selectCidade.innerHTML = sigla
            ? '<option value="">Carregando...</option>'
            : '<option value="">Selecione o estado primeiro</option>';
        if (!sigla) return;
        try {
            const response = await fetch(`https://servicodados.ibge.gov.br/api/v1/localidades/estados/${sigla}/municipios`);
            const cidades = await response.json();
            selectCidade.innerHTML = '<option value="">Todas as cidades</option>';
            cidades.forEach(cidade => {
                const option = document.createElement('option');
                option.value = cidade.nome;
                option.textContent = cidade.nome;
                option.selected = cidade.nome === selectedLocation.cidade;
                selectCidade.appendChild(option);
            });
            selectCidade.disabled = false;
        } catch {
            selectCidade.innerHTML = '<option value="">Não foi possível carregar as cidades</option>';
        }
    }

    selectEstado.addEventListener('change', () => carregarCidades(selectEstado.value));
    carregarEstados();
}
>>>>>>> efea9b9 (Crie a pagina loja no projeto, e a aba petshops foi feita e a pagina cuidadores também, tem alguns erros de design mas pode ser modificado mais tarde)
