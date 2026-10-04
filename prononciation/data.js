// Contenu pédagogique : les difficultés typiques d'un francophone en anglais britannique.
// IPA en anglais britannique standard (SSBE / « RP » moderne).

const TIPS = {
  th_unvoiced: {
    title: "TH sourd /θ/",
    text: "Placez le bout de la langue entre les dents (visible dans un miroir) et soufflez sans faire vibrer la gorge. Ce n'est ni un « s », ni un « f », ni un « t ». Si on entend « sink » au lieu de « think », la langue est restée derrière les dents."
  },
  th_voiced: {
    title: "TH sonore /ð/",
    text: "Même position que le TH sourd (langue entre les dents), mais la gorge vibre, comme un « z » doux. Évitez « ze » et « de » : « the » ne doit pas devenir « ze » ni « de »."
  },
  h_drop: {
    title: "H aspiré oublié",
    text: "En anglais, le H se prononce : c'est un souffle, comme de la buée sur une vitre. Sans ce souffle, « hair » devient « air » et « heat » devient « eat ». Exagérez le souffle au début."
  },
  h_add: {
    title: "H ajouté en trop",
    text: "Vous avez ajouté un souffle devant une voyelle. « Eat », « air », « old » commencent directement par la voyelle, sans souffle. Ne mettez le H que là où il est écrit (sauf « hour », « honest », « honour »)."
  },
  ih_ee: {
    title: "Voyelle courte /ɪ/ ou longue /iː/",
    text: "« Ship » /ɪ/ est court et relâché, entre le « i » et le « é » français, bouche détendue. « Sheep » /iː/ est long et tendu, un « i » français tenu deux fois plus longtemps avec un léger sourire. Les confondre change le mot."
  },
  uu: {
    title: "Voyelle courte /ʊ/ ou longue /uː/",
    text: "« Full » /ʊ/ est court et relâché, lèvres à peine arrondies. « Fool » /uː/ est long, lèvres bien arrondies, comme « ou » tenu longtemps."
  },
  a_vowels: {
    title: "Les trois « a » : /æ/, /ʌ/, /ɑː/",
    text: "« Cat » /æ/ : bouche très ouverte, entre « a » et « è ». « Cut » /ʌ/ : un « a » court et central, proche du « eu » de « peur » mais plus ouvert. « Cart » /ɑː/ : un « a » long venu du fond de la bouche, sans prononcer le R."
  },
  stress: {
    title: "Accent tonique et schwa /ə/",
    text: "En français, toutes les syllabes ont le même poids. En anglais, une syllabe est forte (plus longue, plus aiguë, plus forte) et les autres s'affaiblissent souvent en /ə/, un « e » très bref. Une erreur d'accent rend un mot méconnaissable plus souvent qu'une erreur de son."
  },
  w_v: {
    title: "W /w/ et V /v/",
    text: "W : lèvres arrondies en avant comme pour « ou », sans toucher les dents (« ouest »). V : dents du haut posées sur la lèvre du bas, qui vibre. « Wine » et « vine » sont deux mots différents."
  },
  ed: {
    title: "Terminaison -ed",
    text: "Ne la supprimez pas et ne dites pas « -èd ». Trois sons : /t/ après un son sourd (worked, watched), /d/ après un son sonore (played, called), /ɪd/ seulement après t ou d (wanted, needed)."
  },
  final_s: {
    title: "Consonne finale oubliée",
    text: "En français, les consonnes finales sont souvent muettes. En anglais, elles portent le sens : « he like » au lieu de « he likes », « book » au lieu de « books ». Articulez nettement la dernière consonne."
  },
  r: {
    title: "R britannique",
    text: "Pas de R de gorge. Pour un R devant une voyelle (red, very), reculez la langue sans toucher le palais, lèvres légèrement arrondies. Après une voyelle (car, park, mother), en anglais britannique on ne prononce pas le R du tout : on allonge la voyelle."
  },
  diph: {
    title: "Diphtongues /əʊ/ et /eɪ/",
    text: "Les voyelles anglaises « glissent ». « No » n'est pas « nô » mais /nəʊ/ : « e » bref qui glisse vers « ou ». « Late » n'est pas « lèt » mais /leɪt/ : « é » qui glisse vers « i »."
  },
  ng: {
    title: "Le son -ng /ŋ/",
    text: "Dans « -ing », on n'entend ni un « g » dur ni un « n » français. Le dos de la langue touche le fond du palais (comme dans « parking » à la française) et l'air sort par le nez. Ne dites pas « -inne »."
  },
  vowel: {
    title: "Voyelle à corriger",
    text: "Les consonnes étaient bonnes mais la voyelle a été comprise autrement. Écoutez le modèle au ralenti et faites attention à la longueur de la voyelle : en anglais, voyelle courte ou longue change le mot."
  },
  generic: {
    title: "Mot mal reconnu",
    text: "Écoutez le modèle au ralenti, puis répétez le mot seul avant de le remettre dans la phrase. Vérifiez quelle syllabe est accentuée."
  },
  missing: {
    title: "Mot non entendu",
    text: "Ce mot n'a pas été reconnu. Articulez-le un peu plus et ne vous arrêtez pas avant la fin de la phrase. Les petits mots (a, the, to, of) peuvent être brefs mais doivent rester présents."
  }
};

const LESSONS = [
  {
    id: "th1", tip: "th_unvoiced", title: "TH sourd", sound: "/θ/", sample: "think",
    items: [
      { en: "think", ipa: "θɪŋk" },
      { en: "three", ipa: "θriː" },
      { en: "thank you", ipa: "ˈθæŋk juː" },
      { en: "mouth", ipa: "maʊθ" },
      { en: "birthday", ipa: "ˈbɜːθdeɪ" },
      { en: "Thursday", ipa: "ˈθɜːzdeɪ" },
      { en: "I think it's Thursday.", ipa: "aɪ ˈθɪŋk ɪts ˈθɜːzdeɪ" },
      { en: "Thank you for the three tickets.", ipa: "ˈθæŋk juː fə ðə ˈθriː ˈtɪkɪts" }
    ]
  },
  {
    id: "th2", tip: "th_voiced", title: "TH sonore", sound: "/ð/", sample: "this",
    items: [
      { en: "this", ipa: "ðɪs" },
      { en: "they", ipa: "ðeɪ" },
      { en: "mother", ipa: "ˈmʌðə" },
      { en: "together", ipa: "təˈɡeðə" },
      { en: "breathe", ipa: "briːð" },
      { en: "That's the one.", ipa: "ˈðæts ðə ˈwʌn" },
      { en: "My brother and their father are together.", ipa: "maɪ ˈbrʌðər ən ðeə ˈfɑːðər ə təˈɡeðə" }
    ]
  },
  {
    id: "h", tip: "h_drop", title: "Le H aspiré", sound: "/h/", sample: "house",
    items: [
      { en: "hello", ipa: "həˈləʊ" },
      { en: "house", ipa: "haʊs" },
      { en: "hungry", ipa: "ˈhʌŋɡri" },
      { en: "hair", ipa: "heə" },
      { en: "air", ipa: "eə" },
      { en: "heat", ipa: "hiːt" },
      { en: "eat", ipa: "iːt" },
      { en: "How are you?", ipa: "ˈhaʊ ə juː" },
      { en: "Harry has a huge house in Hampshire.", ipa: "ˈhæri hæz ə ˈhjuːdʒ ˈhaʊs ɪn ˈhæmpʃə" }
    ]
  },
  {
    id: "ih", tip: "ih_ee", title: "Ship ou sheep", sound: "/ɪ/ /iː/", sample: "ship",
    items: [
      { en: "ship", ipa: "ʃɪp" },
      { en: "sheep", ipa: "ʃiːp" },
      { en: "live", ipa: "lɪv" },
      { en: "leave", ipa: "liːv" },
      { en: "sit", ipa: "sɪt" },
      { en: "seat", ipa: "siːt" },
      { en: "fill", ipa: "fɪl" },
      { en: "feel", ipa: "fiːl" },
      { en: "Please sit in this seat.", ipa: "ˈpliːz ˈsɪt ɪn ðɪs ˈsiːt" },
      { en: "I live here but I leave at six.", ipa: "aɪ ˈlɪv ˈhɪə bət aɪ ˈliːv ət ˈsɪks" }
    ]
  },
  {
    id: "uu", tip: "uu", title: "Full ou fool", sound: "/ʊ/ /uː/", sample: "full",
    items: [
      { en: "full", ipa: "fʊl" },
      { en: "fool", ipa: "fuːl" },
      { en: "pull", ipa: "pʊl" },
      { en: "pool", ipa: "puːl" },
      { en: "book", ipa: "bʊk" },
      { en: "good", ipa: "ɡʊd" },
      { en: "Look at the full moon.", ipa: "ˈlʊk ət ðə ˈfʊl ˈmuːn" },
      { en: "Could you put the food in the cupboard?", ipa: "kəd juː ˈpʊt ðə ˈfuːd ɪn ðə ˈkʌbəd" }
    ]
  },
  {
    id: "a", tip: "a_vowels", title: "Cat, cut, cart", sound: "/æ/ /ʌ/ /ɑː/", sample: "cat",
    items: [
      { en: "cat", ipa: "kæt" },
      { en: "cut", ipa: "kʌt" },
      { en: "cart", ipa: "kɑːt" },
      { en: "hat", ipa: "hæt" },
      { en: "hut", ipa: "hʌt" },
      { en: "heart", ipa: "hɑːt" },
      { en: "bag", ipa: "bæɡ" },
      { en: "bug", ipa: "bʌɡ" },
      { en: "My uncle has a black cat.", ipa: "maɪ ˈʌŋkl hæz ə ˈblæk ˈkæt" },
      { en: "Come on, the bus is coming.", ipa: "ˈkʌm ˈɒn ðə ˈbʌs ɪz ˈkʌmɪŋ" }
    ]
  },
  {
    id: "stress", tip: "stress", title: "Accent et schwa", sound: "/ə/", sample: "banana",
    items: [
      { en: "banana", ipa: "bəˈnɑːnə" },
      { en: "comfortable", ipa: "ˈkʌmftəbl" },
      { en: "vegetable", ipa: "ˈvedʒtəbl" },
      { en: "photograph", ipa: "ˈfəʊtəɡrɑːf" },
      { en: "photographer", ipa: "fəˈtɒɡrəfə" },
      { en: "interesting", ipa: "ˈɪntrəstɪŋ" },
      { en: "development", ipa: "dɪˈveləpmənt" },
      { en: "I'd like a cup of tea.", ipa: "aɪd ˈlaɪk ə ˈkʌp əv ˈtiː" },
      { en: "What do you want to do?", ipa: "ˈwɒt də jə ˈwɒnt tə ˈduː" }
    ]
  },
  {
    id: "wv", tip: "w_v", title: "W et V", sound: "/w/ /v/", sample: "wine",
    items: [
      { en: "wine", ipa: "waɪn" },
      { en: "vine", ipa: "vaɪn" },
      { en: "west", ipa: "west" },
      { en: "vest", ipa: "vest" },
      { en: "woman", ipa: "ˈwʊmən" },
      { en: "would", ipa: "wʊd" },
      { en: "We were very well.", ipa: "wi wə ˈveri ˈwel" },
      { en: "Victor wears a white vest.", ipa: "ˈvɪktə ˈweəz ə ˈwaɪt ˈvest" }
    ]
  },
  {
    id: "ed", tip: "ed", title: "Les terminaisons -ed", sound: "/t/ /d/ /ɪd/", sample: "worked",
    items: [
      { en: "worked", ipa: "wɜːkt" },
      { en: "played", ipa: "pleɪd" },
      { en: "wanted", ipa: "ˈwɒntɪd" },
      { en: "watched", ipa: "wɒtʃt" },
      { en: "needed", ipa: "ˈniːdɪd" },
      { en: "I walked home yesterday.", ipa: "aɪ ˈwɔːkt ˈhəʊm ˈjestədeɪ" },
      { en: "She looked tired and wanted to rest.", ipa: "ʃi ˈlʊkt ˈtaɪəd ən ˈwɒntɪd tə ˈrest" }
    ]
  },
  {
    id: "final", tip: "final_s", title: "Consonnes finales", sound: "/s/ /z/ /t/", sample: "likes",
    items: [
      { en: "likes", ipa: "laɪks" },
      { en: "books", ipa: "bʊks" },
      { en: "dogs", ipa: "dɒɡz" },
      { en: "next", ipa: "nekst" },
      { en: "He likes it.", ipa: "hi ˈlaɪks ɪt" },
      { en: "She needs three books.", ipa: "ʃi ˈniːdz ˈθriː ˈbʊks" },
      { en: "It costs eight pounds.", ipa: "ɪt ˈkɒsts ˈeɪt ˈpaʊndz" }
    ]
  },
  {
    id: "r", tip: "r", title: "Le R britannique", sound: "/r/", sample: "red",
    items: [
      { en: "red", ipa: "red" },
      { en: "very", ipa: "ˈveri" },
      { en: "car", ipa: "kɑː" },
      { en: "water", ipa: "ˈwɔːtə" },
      { en: "first", ipa: "fɜːst" },
      { en: "The car is parked far away.", ipa: "ðə ˈkɑːr ɪz ˈpɑːkt ˈfɑːr əˈweɪ" },
      { en: "Rory runs round the park.", ipa: "ˈrɔːri ˈrʌnz ˈraʊnd ðə ˈpɑːk" }
    ]
  },
  {
    id: "diph", tip: "diph", title: "Diphtongues", sound: "/əʊ/ /eɪ/", sample: "home",
    items: [
      { en: "no", ipa: "nəʊ" },
      { en: "home", ipa: "həʊm" },
      { en: "phone", ipa: "fəʊn" },
      { en: "late", ipa: "leɪt" },
      { en: "make", ipa: "meɪk" },
      { en: "Don't go home alone.", ipa: "ˈdəʊnt ɡəʊ ˈhəʊm əˈləʊn" },
      { en: "Wait, take the train.", ipa: "ˈweɪt ˈteɪk ðə ˈtreɪn" }
    ]
  },
  {
    id: "ng", tip: "ng", title: "Le son -ing", sound: "/ŋ/", sample: "morning",
    items: [
      { en: "singing", ipa: "ˈsɪŋɪŋ" },
      { en: "morning", ipa: "ˈmɔːnɪŋ" },
      { en: "thinking", ipa: "ˈθɪŋkɪŋ" },
      { en: "young", ipa: "jʌŋ" },
      { en: "I'm going shopping this evening.", ipa: "aɪm ˈɡəʊɪŋ ˈʃɒpɪŋ ðɪs ˈiːvnɪŋ" }
    ]
  },
  {
    id: "daily", tip: "stress", title: "Phrases du quotidien", sound: "UK", sample: "please",
    items: [
      { en: "Could I have the bill, please?", ipa: "kəd aɪ ˈhæv ðə ˈbɪl ˈpliːz" },
      { en: "Excuse me, where is the nearest station?", ipa: "ɪkˈskjuːz mi ˈweər ɪz ðə ˈnɪərɪst ˈsteɪʃn" },
      { en: "Would you like a cup of tea?", ipa: "wəd jə ˈlaɪk ə ˈkʌp əv ˈtiː" },
      { en: "It's a bit chilly this morning.", ipa: "ɪts ə ˈbɪt ˈtʃɪli ðɪs ˈmɔːnɪŋ" },
      { en: "I'm afraid I can't make it on Thursday.", ipa: "aɪm əˈfreɪd aɪ ˈkɑːnt ˈmeɪk ɪt ɒn ˈθɜːzdeɪ" },
      { en: "Sorry, could you say that again?", ipa: "ˈsɒri kəd jə ˈseɪ ˈðæt əˈɡen" },
      { en: "I'd like to book a table for two.", ipa: "aɪd ˈlaɪk tə ˈbʊk ə ˈteɪbl fə ˈtuː" },
      { en: "How much does this cost?", ipa: "ˈhaʊ ˈmʌtʃ dəz ðɪs ˈkɒst" }
    ]
  }
];

// Paires minimales : si le mot visé est compris comme l'autre, on sait quel son corriger.
const MINIMAL_PAIRS = [
  ["ship", "sheep", "ih_ee"], ["live", "leave", "ih_ee"], ["sit", "seat", "ih_ee"],
  ["fill", "feel", "ih_ee"], ["it", "eat", "ih_ee"], ["is", "ease", "ih_ee"], ["his", "he's", "ih_ee"],
  ["full", "fool", "uu"], ["pull", "pool", "uu"], ["look", "luke", "uu"], ["could", "cooled", "uu"],
  ["cat", "cut", "a_vowels"], ["cat", "cart", "a_vowels"], ["cut", "cart", "a_vowels"],
  ["hat", "hut", "a_vowels"], ["hat", "heart", "a_vowels"], ["hut", "heart", "a_vowels"],
  ["bag", "bug", "a_vowels"], ["cap", "cup", "a_vowels"], ["uncle", "ankle", "a_vowels"],
  ["wine", "vine", "w_v"], ["west", "vest", "w_v"], ["wet", "vet", "w_v"], ["worse", "verse", "w_v"],
  ["no", "now", "diph"], ["home", "hum", "diph"], ["late", "let", "diph"], ["make", "mac", "diph"],
  ["phone", "fun", "diph"], ["wait", "wet", "diph"], ["coat", "caught", "diph"],
  ["red", "wed", "r"], ["very", "wary", "r"], ["right", "white", "r"], ["first", "fast", "r"],
  ["think", "sink", "th_unvoiced"], ["think", "fink", "th_unvoiced"], ["three", "free", "th_unvoiced"],
  ["three", "tree", "th_unvoiced"], ["thank", "sank", "th_unvoiced"], ["thank", "tank", "th_unvoiced"],
  ["mouth", "mouse", "th_unvoiced"], ["thin", "sin", "th_unvoiced"], ["thin", "fin", "th_unvoiced"],
  ["they", "day", "th_voiced"], ["breathe", "breeze", "th_voiced"], ["then", "zen", "th_voiced"],
  ["those", "doze", "th_voiced"], ["there", "dare", "th_voiced"]
];

// Mots qui se prononcent pareil : les confondre n'est pas une erreur de prononciation.
const HOMOPHONES = [
  ["weather", "whether"], ["hear", "here"], ["their", "there", "they're"], ["to", "too", "two"],
  ["for", "four"], ["see", "sea"], ["meet", "meat"], ["right", "write"], ["no", "know"],
  ["new", "knew"], ["son", "sun"], ["by", "buy", "bye"], ["would", "wood"], ["whole", "hole"],
  ["hour", "our"], ["flower", "flour"], ["i", "eye"], ["be", "bee"], ["piece", "peace"],
  ["wear", "where"], ["which", "witch"], ["made", "maid"], ["plane", "plain"], ["week", "weak"],
  ["one", "won"], ["eight", "ate"], ["sale", "sail"], ["tale", "tail"], ["road", "rode"],
  ["ok", "okay"], ["colour", "color"], ["favourite", "favorite"], ["mum", "mom"],
  ["read", "red"], ["heal", "heel", "he'll"], ["air", "heir"], ["higher", "hire"], ["fare", "fair"]
];

const VOICED_TH = new Set(["the", "this", "that", "that's", "these", "those", "they", "them", "their", "there",
  "then", "than", "though", "mother", "father", "brother", "other", "another", "together", "weather",
  "with", "breathe", "clothes", "either", "neither", "rather", "without", "although"]);

// Espaces insécables dans les guillemets français, pour qu'ils ne se retrouvent pas seuls en bout de ligne.
Object.values(TIPS).forEach(t => { t.text = t.text.replace(/« /g, "« ").replace(/ »/g, " »"); });
