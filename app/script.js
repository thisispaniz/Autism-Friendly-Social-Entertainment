const questionEl = document.getElementById('question');
const options = document.querySelectorAll('.options input');
const submitBtn = document.getElementById('submit');
const resultEl = document.getElementById('result');

const questions = [
    {
        question: "What level of noise are you willing to tolerate?",
        answers: [
            { text: "A. Low", correct: false },
            { text: "B. Medium", correct: true },
            { text: "C. High", correct: false }
        ]
    },
    // Add more questions here in the same format 
];

let currentQuestion = 0;
let score = 0;

function loadQuestion() {
    deselectAnswers(); // Reset selected options

    const currentQuestionData = questions[currentQuestion];

    questionEl.innerText = currentQuestionData.question;
    currentQuestionData.answers.forEach((answer, index) => {
        const option = options[index];
        option.value = answer.text;
        option.nextElementSibling.innerText = answer.text;
    });
}

function deselectAnswers() {
    options.forEach(option => option.checked = false);
}

function getSelected() {
    let selectedAnswer;
    options.forEach(option => {
        if (option.checked) {
            selectedAnswer = option.value;
        }
    });
    return selectedAnswer;
}

submitBtn.addEventListener('click', () => {
    const answer = getSelected();
    if (answer) {
        if (questions[currentQuestion].answers.find(a => a.text === answer).correct) {
            score++;
        }
        currentQuestion++;
        if (currentQuestion < questions.length) {
            loadQuestion();
        } else {
            resultEl.innerHTML = `<h2>You answered ${score}/${questions.length} questions correctly</h2> 
                                  <button onclick="location.reload()">Reload</button>`;
        }
    }
});

loadQuestion();

// password stuff
let passwordInp = document.querySelector('.password-input');
let passwordChecklist = document.querySelectorAll('.list-item');


let validationRegex = [
    { regex: /.{8,}/ },
    { regex: /[0-9]/ },
    { regex: /[a-z]/},
    { regex: /[A-Z]/},
    { regex: /[^A-Za-z0-9]/ } 
];

passwordInp.addEventListener('keyup', () => {
    validationRegex.forEach((item, i) => {
        let isValid = item.regex.test(passwordInp.value);

        if (isValid) {
            passwordChecklist[i].classList.add('checked');
        } else {
            passwordChecklist[i].classList.remove('checked');
        }
    });
});

function myFunction() {
    // Declare variables
    var input, filter, table, tr, td, i, txtValue;
    input = document.getElementById("myInput");
    filter = input.value.toUpperCase();
    table = document.getElementById("myTable");
    tr = table.getElementsByTagName("tr");
  
}