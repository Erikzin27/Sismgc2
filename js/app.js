import { db } from './firebase-config.js';
import { collection, addDoc, deleteDoc, doc, onSnapshot, query, orderBy } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

const form = document.getElementById('registro-form');
const tabela = document.getElementById('tabela-corpo');

// 1. SALVAR NO BANCO DE DADOS
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const dados = {
        data: document.getElementById('data').value,
        tipo: document.getElementById('tipo').value,
        descricao: document.getElementById('descricao').value,
        valor: parseFloat(document.getElementById('valor').value),
        criadoEm: new Date() // Para ordenar corretamente
    };

    try {
        await addDoc(collection(db, "movimentacoes"), dados);
        form.reset(); // Limpa o formulário
    } catch (error) {
        console.error("Erro ao salvar:", error);
        alert("Erro ao salvar o registro.");
    }
});

// 2. LER DADOS EM TEMPO REAL (Atualiza sozinho)
const q = query(collection(db, "movimentacoes"), orderBy("data", "desc"));

onSnapshot(q, (snapshot) => {
    tabela.innerHTML = ''; // Limpa a tabela antes de recriar

    snapshot.forEach((docSnapshot) => {
        const registro = docSnapshot.data();
        const id = docSnapshot.id; // ID único do documento no Firebase

        // Formatação do valor (R$ ou Unid)
        let valorFormatado;
        if (registro.tipo === 'producao') {
            valorFormatado = `${registro.valor} Unid.`;
        } else {
            valorFormatado = registro.valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        }

        // Cria a linha da tabela (HTML)
        const linha = `
            <tr>
                <td>${formatarData(registro.data)}</td>
                <td class="tipo-${registro.tipo}">${registro.tipo.toUpperCase()}</td>
                <td>${registro.descricao}</td>
                <td>${valorFormatado}</td>
                <td>
                    <button class="btn-delete" onclick="window.deletarRegistro('${id}')">Excluir</button>
                </td>
            </tr>
        `;
        tabela.innerHTML += linha;
    });
});

// 3. EXCLUIR REGISTRO
// Precisamos colocar no 'window' para o HTML conseguir acessar a função
window.deletarRegistro = async (id) => {
    if(confirm("Tem certeza que deseja apagar?")) {
        try {
            await deleteDoc(doc(db, "movimentacoes", id));
        } catch (error) {
            console.error("Erro ao excluir:", error);
        }
    }
}

// Função auxiliar para formatar a data (2023-12-01 -> 01/12/2023)
function formatarData(dataAmericana) {
    const dataParts = dataAmericana.split('-');
    return `${dataParts[2]}/${dataParts[1]}/${dataParts[0]}`;
}