package com.usernamemp.englishsprint;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Random;

public final class QuestionBank {
    public static final String[] SKILLS = {
            "be", "have_has", "do_does", "articles", "pronouns",
            "present_simple", "present_continuous", "past_simple", "past_continuous",
            "prepositions", "comparison", "some_any", "olympiad_grammar",
            "reading", "listening", "story"
    };

    private static List<Question> CACHE;

    private QuestionBank() {}

    public static List<Question> all() {
        if (CACHE == null) {
            List<Question> q = new ArrayList<>();
            addBe(q);
            addHaveHas(q);
            addDoDoes(q);
            addArticles(q);
            addPronouns(q);
            addPresentSimple(q);
            addPresentContinuous(q);
            addPastSimple(q);
            addPastContinuous(q);
            addPrepositions(q);
            addComparison(q);
            addSomeAny(q);
            addOlympiadGrammar(q);
            addReading(q);
            addListening(q);
            addStory(q);
            CACHE = Collections.unmodifiableList(q);
        }
        return CACHE;
    }

    public static List<Question> byType(Question.Type type) {
        List<Question> result = new ArrayList<>();
        for (Question q : all()) if (q.type == type) result.add(q);
        return result;
    }

    public static List<Question> adaptiveSession(ProgressStore progress, int count, long seed) {
        List<Question> pool = new ArrayList<>(all());
        Random random = new Random(seed);
        Collections.shuffle(pool, random);
        // Collections.sort is stable, so shuffling first randomizes ties without
        // using a non-deterministic comparator.
        pool.sort((a, b) -> Double.compare(
                progress.mastery(a.skill),
                progress.mastery(b.skill)));

        // Keep the short session broad: no single weak skill may consume the entire run.
        List<Question> result = new ArrayList<>();
        List<String> recentSkills = new ArrayList<>();
        for (Question q : pool) {
            int same = 0;
            for (String s : recentSkills) if (s.equals(q.skill)) same++;
            if (same >= 3) continue;
            result.add(q);
            recentSkills.add(q.skill);
            if (recentSkills.size() > 8) recentSkills.remove(0);
            if (result.size() >= count) break;
        }
        return result;
    }

    public static List<Question> sprint(int count, long seed) {
        List<Question> result = new ArrayList<>();
        addRandomFrom(result, Question.Type.LISTENING, 3, seed + 1);
        addRandomFrom(result, Question.Type.READING, 4, seed + 2);
        addRandomFrom(result, Question.Type.GRAMMAR, 10, seed + 3);
        addRandomFrom(result, Question.Type.STORY, 5, seed + 4);
        Collections.shuffle(result, new Random(seed + 5));
        if (result.size() > count) return new ArrayList<>(result.subList(0, count));
        return result;
    }

    private static void addRandomFrom(List<Question> out, Question.Type type, int count, long seed) {
        List<Question> list = byType(type);
        Collections.shuffle(list, new Random(seed));
        out.addAll(list.subList(0, Math.min(count, list.size())));
    }

    private static Question q(String id, String skill, Question.Type type, String prompt,
                              String context, int answer, String explanation, String evidence,
                              String audioAsset, String speechText, String... options) {
        return new Question(id, skill, type, prompt, context, answer, explanation, evidence,
                audioAsset, speechText, options);
    }

    private static void addBe(List<Question> out) {
        String[][] rows = {
                {"I ___ ten years old.", "am", "is", "are", "0"},
                {"My sister ___ at school.", "am", "is", "are", "1"},
                {"We ___ ready.", "am", "is", "are", "2"},
                {"The dogs ___ hungry.", "am", "is", "are", "2"},
                {"It ___ cold today.", "am", "is", "are", "1"},
                {"You ___ my best friend.", "am", "is", "are", "2"},
                {"Tom and I ___ in class 5A.", "am", "is", "are", "2"},
                {"This book ___ interesting.", "am", "is", "are", "1"}
        };
        for (int i = 0; i < rows.length; i++) {
            String[] r = rows[i];
            out.add(q("be_" + i, "be", Question.Type.GRAMMAR, r[0], "", Integer.parseInt(r[4]),
                    "I → am; he/she/it → is; you/we/they → are.", "", "", "",
                    r[1], r[2], r[3]));
        }

        String[][] past = {
                {"Yesterday I ___ tired.", "was", "were", "am", "0"},
                {"They ___ at the cinema last night.", "was", "were", "are", "1"},
                {"The weather ___ sunny on Sunday.", "was", "were", "is", "0"},
                {"We ___ late for school.", "was", "were", "are", "1"}
        };
        for (int i = 0; i < past.length; i++) {
            String[] r = past[i];
            out.add(q("be_past_" + i, "be", Question.Type.GRAMMAR, r[0], "", Integer.parseInt(r[4]),
                    "Past of be: I/he/she/it → was; you/we/they → were.", "", "", "",
                    r[1], r[2], r[3]));
        }
    }

    private static void addHaveHas(List<Question> out) {
        String[][] rows = {
                {"I ___ a blue backpack.", "have", "has", "am", "0"},
                {"She ___ two brothers.", "have", "has", "is", "1"},
                {"My dog ___ long ears.", "have", "has", "is", "1"},
                {"We ___ English on Monday.", "have", "has", "are", "0"},
                {"Peter and Ann ___ a new teacher.", "have", "has", "are", "0"},
                {"The house ___ three windows.", "have", "has", "is", "1"},
                {"You ___ a good idea.", "have", "has", "are", "0"},
                {"His friend ___ a bicycle.", "have", "has", "is", "1"},
                {"These books ___ colourful pictures.", "have", "has", "are", "0"},
                {"My mum ___ a meeting today.", "have", "has", "is", "1"}
        };
        for (int i = 0; i < rows.length; i++) {
            String[] r = rows[i];
            out.add(q("have_" + i, "have_has", Question.Type.GRAMMAR, r[0], "",
                    Integer.parseInt(r[4]), "I/you/we/they → have; he/she/it → has.", "", "", "",
                    r[1], r[2], r[3]));
        }
    }

    private static void addDoDoes(List<Question> out) {
        String[][] rows = {
                {"___ you like chess?", "Do", "Does", "Are", "0"},
                {"___ Kate play tennis?", "Do", "Does", "Is", "1"},
                {"___ they live near school?", "Do", "Does", "Are", "0"},
                {"___ your brother read comics?", "Do", "Does", "Is", "1"},
                {"I ___ not watch TV in the morning.", "do", "does", "am", "0"},
                {"He ___ not eat meat.", "do", "does", "is", "1"},
                {"What ___ she do after school?", "do", "does", "is", "1"},
                {"Where ___ your friends meet?", "do", "does", "are", "0"}
        };
        for (int i = 0; i < rows.length; i++) {
            String[] r = rows[i];
            out.add(q("do_" + i, "do_does", Question.Type.GRAMMAR, r[0], "",
                    Integer.parseInt(r[4]), "Present Simple questions: do with I/you/we/they; does with he/she/it.", "", "", "",
                    r[1], r[2], r[3]));
        }
    }

    private static void addArticles(List<Question> out) {
        String[][] rows = {
                {"I can see ___ cat in the garden.", "a", "an", "the", "0"},
                {"She has ___ orange umbrella.", "a", "an", "the", "1"},
                {"Close ___ door, please.", "a", "an", "the", "2"},
                {"My dad is ___ engineer.", "a", "an", "the", "1"},
                {"We saw ___ moon last night.", "a", "an", "the", "2"},
                {"He wants ___ new computer.", "a", "an", "the", "0"},
                {"There is ___ apple on the table.", "a", "an", "the", "1"},
                {"___ sun is very bright today.", "A", "An", "The", "2"},
                {"I need ___ hour to finish this.", "a", "an", "the", "1"},
                {"She is reading ___ book I gave her.", "a", "an", "the", "2"},
                {"He bought ___ sandwich for lunch.", "a", "an", "the", "0"},
                {"This is ___ easiest task.", "a", "an", "the", "2"}
        };
        for (int i = 0; i < rows.length; i++) {
            String[] r = rows[i];
            out.add(q("article_" + i, "articles", Question.Type.GRAMMAR, r[0], "",
                    Integer.parseInt(r[4]), "a before a consonant sound; an before a vowel sound; the for a specific or unique thing.", "", "", "",
                    r[1], r[2], r[3]));
        }
    }

    private static void addPronouns(List<Question> out) {
        out.add(q("pro_1", "pronouns", Question.Type.GRAMMAR,
                "Anna is my friend. I see ___ every day.", "", 1,
                "After a verb use the object form: she → her.", "", "", "",
                "she", "her", "hers"));
        out.add(q("pro_2", "pronouns", Question.Type.GRAMMAR,
                "This is Tom. ___ bike is red.", "", 2,
                "Before a noun use a possessive adjective: his bike.", "", "", "",
                "He", "Him", "His"));
        out.add(q("pro_3", "pronouns", Question.Type.GRAMMAR,
                "My parents are at home. ___ are cooking dinner.", "", 0,
                "Parents = they.", "", "", "",
                "They", "Them", "Their"));
        out.add(q("pro_4", "pronouns", Question.Type.GRAMMAR,
                "We have a dog. ___ name is Lucky.", "", 1,
                "For an animal/thing before a noun: its.", "", "", "",
                "It", "Its", "It's"));
        out.add(q("pro_5", "pronouns", Question.Type.GRAMMAR,
                "Can you help ___?", "", 1,
                "After help use the object form: me.", "", "", "",
                "I", "me", "my"));
        out.add(q("pro_6", "pronouns", Question.Type.GRAMMAR,
                "These pencils belong to Kate and me. They are ___.", "", 2,
                "A possessive pronoun can stand alone: ours.", "", "", "",
                "our", "us", "ours"));
    }

    private static void addPresentSimple(List<Question> out) {
        String[][] rows = {
                {"My brother ___ football every Saturday.", "play", "plays", "is playing", "1"},
                {"I usually ___ breakfast at seven.", "have", "has", "am having", "0"},
                {"Cats ___ milk.", "likes", "like", "are liking", "1"},
                {"She ___ to school by bus.", "go", "goes", "is going", "1"},
                {"We ___ English twice a week.", "study", "studies", "are studying", "0"},
                {"The shop ___ at nine.", "open", "opens", "is opening", "1"},
                {"Dad always ___ coffee in the morning.", "drink", "drinks", "is drinking", "1"},
                {"They often ___ in the park.", "walk", "walks", "are walking", "0"}
        };
        for (int i = 0; i < rows.length; i++) {
            String[] r = rows[i];
            out.add(q("ps_" + i, "present_simple", Question.Type.GRAMMAR, r[0], "",
                    Integer.parseInt(r[4]), "Present Simple: habits and facts. With he/she/it add -s/-es.", "", "", "",
                    r[1], r[2], r[3]));
        }
    }

    private static void addPresentContinuous(List<Question> out) {
        String[][] rows = {
                {"Look! The baby ___ .", "sleeps", "is sleeping", "sleep", "1"},
                {"We ___ dinner right now.", "have", "are having", "has", "1"},
                {"Listen! Someone ___ the piano.", "plays", "is playing", "play", "1"},
                {"I ___ my homework at the moment.", "do", "am doing", "does", "1"},
                {"The children ___ outside now.", "run", "are running", "runs", "1"},
                {"Why ___ you laughing?", "do", "are", "is", "1"}
        };
        for (int i = 0; i < rows.length; i++) {
            String[] r = rows[i];
            out.add(q("pc_" + i, "present_continuous", Question.Type.GRAMMAR, r[0], "",
                    Integer.parseInt(r[4]), "Present Continuous: am/is/are + verb-ing for an action happening now.", "", "", "",
                    r[1], r[2], r[3]));
        }
    }

    private static void addPastSimple(List<Question> out) {
        String[][] rows = {
                {"Yesterday we ___ to the zoo.", "go", "went", "gone", "1"},
                {"She ___ a funny story last night.", "tells", "told", "tell", "1"},
                {"I ___ my keys this morning.", "lose", "lost", "losed", "1"},
                {"They ___ a film on Friday.", "watch", "watched", "watching", "1"},
                {"Tom ___ breakfast at eight.", "eat", "ate", "eaten", "1"},
                {"My friend ___ me after school.", "called", "calls", "calling", "0"},
                {"We ___ a snowman yesterday.", "make", "made", "maked", "1"},
                {"The lesson ___ at ten.", "start", "started", "starts", "1"}
        };
        for (int i = 0; i < rows.length; i++) {
            String[] r = rows[i];
            out.add(q("past_" + i, "past_simple", Question.Type.GRAMMAR, r[0], "",
                    Integer.parseInt(r[4]), "Past Simple is used for a finished past action. Learn common irregular forms.", "", "", "",
                    r[1], r[2], r[3]));
        }
    }

    private static void addPastContinuous(List<Question> out) {
        String[][] rows = {
                {"At 7 p.m. I ___ my homework.", "did", "was doing", "am doing", "1"},
                {"They ___ football when it started to rain.", "played", "were playing", "play", "1"},
                {"Mum ___ dinner while I was reading.", "cooked", "was cooking", "cooks", "1"},
                {"We ___ home when we saw the accident.", "were walking", "walked", "are walking", "0"},
                {"What ___ you doing at six?", "was", "were", "did", "1"},
                {"The dog ___ while the baby was sleeping.", "was barking", "barked", "is barking", "0"}
        };
        for (int i = 0; i < rows.length; i++) {
            String[] r = rows[i];
            out.add(q("past_cont_" + i, "past_continuous", Question.Type.GRAMMAR, r[0], "",
                    Integer.parseInt(r[4]), "Past Continuous: was/were + verb-ing for an action in progress in the past.", "", "", "",
                    r[1], r[2], r[3]));
        }
    }

    private static void addPrepositions(List<Question> out) {
        String[][] rows = {
                {"The lesson starts ___ 9 o'clock.", "in", "on", "at", "2"},
                {"My birthday is ___ May.", "in", "on", "at", "0"},
                {"We have PE ___ Monday.", "in", "on", "at", "1"},
                {"The cat is ___ the table.", "under", "between", "through", "0"},
                {"She walked ___ school with her friend.", "to", "at", "on", "0"},
                {"We came home ___ the film.", "after", "during", "until", "0"},
                {"Wash your hands ___ dinner.", "before", "from", "between", "0"},
                {"The park is ___ the bank and the school.", "between", "under", "at", "0"},
                {"He travelled ___ train.", "by", "on", "with", "0"},
                {"I got a message ___ my teacher.", "from", "to", "at", "0"}
        };
        for (int i = 0; i < rows.length; i++) {
            String[] r = rows[i];
            out.add(q("prep_" + i, "prepositions", Question.Type.GRAMMAR, r[0], "",
                    Integer.parseInt(r[4]), "Learn prepositions in chunks: at 9, in May, on Monday, by train.", "", "", "",
                    r[1], r[2], r[3]));
        }
    }

    private static void addComparison(List<Question> out) {
        String[][] rows = {
                {"A train is usually ___ than a bus.", "fast", "faster", "fastest", "1"},
                {"This is the ___ book in the series.", "funny", "funnier", "funniest", "2"},
                {"My bag is ___ than yours.", "heavy", "heavier", "heaviest", "1"},
                {"Today is ___ than yesterday.", "good", "better", "best", "1"},
                {"This task is not as ___ as the last one.", "difficult", "more difficult", "most difficult", "0"},
                {"Who is the ___ runner in your class?", "fast", "faster", "fastest", "2"}
        };
        for (int i = 0; i < rows.length; i++) {
            String[] r = rows[i];
            out.add(q("cmp_" + i, "comparison", Question.Type.GRAMMAR, r[0], "",
                    Integer.parseInt(r[4]), "Use comparative with than; superlative with the. good → better → best.", "", "", "",
                    r[1], r[2], r[3]));
        }
    }

    private static void addSomeAny(List<Question> out) {
        String[][] rows = {
                {"There are ___ apples in the bag.", "some", "any", "much", "0"},
                {"Have you got ___ brothers?", "some", "any", "much", "1"},
                {"We don't have ___ milk.", "some", "any", "many", "1"},
                {"How ___ books did you buy?", "much", "many", "any", "1"},
                {"How ___ water do you drink?", "much", "many", "some", "0"},
                {"Can I have ___ juice, please?", "some", "any", "many", "0"}
        };
        for (int i = 0; i < rows.length; i++) {
            String[] r = rows[i];
            out.add(q("quant_" + i, "some_any", Question.Type.GRAMMAR, r[0], "",
                    Integer.parseInt(r[4]), "some is common in positive statements and offers; any in questions/negatives. many = countable; much = uncountable.", "", "", "",
                    r[1], r[2], r[3]));
        }
    }

    private static void addOlympiadGrammar(List<Question> out) {
        out.add(q("og_1", "olympiad_grammar", Question.Type.GRAMMAR,
                "I have lived here ___ three years.", "", 1,
                "Present Perfect duration: for + period of time; since + starting point.", "", "", "",
                "since", "for", "from"));
        out.add(q("og_2", "olympiad_grammar", Question.Type.GRAMMAR,
                "She has known him ___ 2022.", "", 0,
                "Use since with a starting point.", "", "", "",
                "since", "for", "during"));
        out.add(q("og_3", "olympiad_grammar", Question.Type.GRAMMAR,
                "We ___ to play outside every evening when we were younger.", "", 1,
                "used to + verb describes a past habit/state that is no longer true.", "", "", "",
                "use", "used", "were used"));
        out.add(q("og_4", "olympiad_grammar", Question.Type.GRAMMAR,
                "If it rains, we ___ at home.", "", 2,
                "First conditional: If + Present Simple, will + verb.", "", "", "",
                "stayed", "stay", "will stay"));
        out.add(q("og_5", "olympiad_grammar", Question.Type.GRAMMAR,
                "Before ___ to bed, I brush my teeth.", "", 0,
                "After a preposition such as before/after, -ing is common.", "", "", "",
                "going", "go", "to go"));
        out.add(q("og_6", "olympiad_grammar", Question.Type.GRAMMAR,
                "I went to the kitchen ___ get some water.", "", 2,
                "Use to + infinitive to express purpose.", "", "", "",
                "for", "by", "to"));
        out.add(q("og_7", "olympiad_grammar", Question.Type.GRAMMAR,
                "He has never ___ this film.", "", 1,
                "Present Perfect: have/has + past participle (V3).", "", "", "",
                "saw", "seen", "see"));
        out.add(q("og_8", "olympiad_grammar", Question.Type.GRAMMAR,
                "This puzzle is ___ than the first one.", "", 0,
                "Comparative form before than.", "", "", "",
                "more difficult", "most difficult", "difficult"));
    }

    private static void addReading(List<Question> out) {
        String p1 = "Mia wanted a quiet place to read after school. The library was crowded, so she walked to the small park behind the museum. She sat on a bench under a large tree and finished two chapters before dinner.";
        out.add(q("read_1", "reading", Question.Type.READING,
                "Why did Mia go to the park?", p1, 1,
                "The correct answer is a paraphrase: the library was crowded, so she needed another quiet place.",
                "The library was crowded, so she walked to the small park behind the museum.", "", "",
                "She wanted to meet a friend.", "The library was too crowded.", "The museum was closed."));
        out.add(q("read_2", "reading", Question.Type.READING,
                "Where did Mia sit?", p1, 2,
                "Find the exact evidence, then match the meaning.", "She sat on a bench under a large tree.", "", "",
                "Inside the museum.", "On the grass.", "On a bench under a tree."));

        String p2 = "Leo's class planned a picnic for Saturday. On Friday evening the weather forecast changed and heavy rain was expected. Their teacher moved the picnic to Sunday. Sunday morning was cool but dry, and everyone brought warm jackets.";
        out.add(q("read_3", "reading", Question.Type.READING,
                "Why was the picnic moved?", p2, 0,
                "Expected heavy rain caused the change.", "heavy rain was expected", "", "",
                "Because of the weather forecast.", "Because the teacher was ill.", "Because nobody had food."));
        out.add(q("read_4", "reading", Question.Type.READING,
                "Which statement is TRUE?", p2, 1,
                "Sunday was cool and dry.", "Sunday morning was cool but dry", "", "",
                "It rained all Sunday.", "The class went on Sunday.", "They did not take jackets."));

        String p3 = "Nora found a small wallet near the sports centre. There was no money inside, but there was a student card with a name on it. Nora gave the wallet to the receptionist. Twenty minutes later a worried boy came back looking for it.";
        out.add(q("read_5", "reading", Question.Type.READING,
                "How could they identify the owner?", p3, 2,
                "The student card contained a name.", "there was a student card with a name on it", "", "",
                "There was a phone number.", "There was money inside.", "There was a student card."));
        out.add(q("read_6", "reading", Question.Type.READING,
                "What did Nora do with the wallet?", p3, 0,
                "She handed it to the receptionist.", "Nora gave the wallet to the receptionist.", "", "",
                "She gave it to the receptionist.", "She took it home.", "She left it outside."));

        String p4 = "Ben loves science but does not enjoy scary films. He wants to watch something funny with his younger sister. The film should be shorter than two hours and suitable for children.";
        out.add(q("read_7", "reading", Question.Type.READING,
                "Which film description fits Ben best?", p4, 1,
                "Match all constraints, not just one keyword.", "funny with his younger sister. The film should be shorter than two hours and suitable for children.", "", "",
                "A 150-minute horror film about a laboratory.",
                "A 95-minute family comedy about young inventors.",
                "A two-hour documentary with no story."));
        out.add(q("read_8", "reading", Question.Type.READING,
                "Which detail is NOT a requirement?", p4, 2,
                "The text says science, funny, younger sister, under two hours and child-suitable. It says nothing about animation.", "", "", "",
                "Suitable for children.", "Shorter than two hours.", "It must be animated."));

        String p5 = "The school chess club meets every Wednesday at four. New players may come even if they do not know all the rules. This week the meeting will start thirty minutes later because the hall is being used for a concert rehearsal.";
        out.add(q("read_9", "reading", Question.Type.READING,
                "What time will the chess club start this week?", p5, 2,
                "Normal time is 4:00; thirty minutes later is 4:30.", "This week the meeting will start thirty minutes later", "", "",
                "3:30", "4:00", "4:30"));
        out.add(q("read_10", "reading", Question.Type.READING,
                "Who may join the club?", p5, 0,
                "Beginners are allowed.", "New players may come even if they do not know all the rules.", "", "",
                "Beginners too.", "Only tournament winners.", "Only students who know every rule."));
    }

    private static void addListening(List<Question> out) {
        listening(out, 1,
                "What should the boy bring tomorrow?",
                "Don't forget your sports clothes tomorrow. We have P.E. before lunch, and your trainers are already in your locker.",
                0, "He needs sports clothes; the trainers are already at school.",
                "Sports clothes", "A lunch box", "New trainers");
        listening(out, 2,
                "What time will they meet?",
                "The film starts at four fifteen. Let's meet outside the cinema at a quarter to four, so we have enough time.",
                1, "A quarter to four means 3:45.",
                "3:30", "3:45", "4:15");
        listening(out, 3,
                "Where is the girl's notebook?",
                "I thought my notebook was in my school bag, but Dad found it on the kitchen table next to my water bottle.",
                2, "Dad found it on the kitchen table.",
                "In her school bag", "In her bedroom", "On the kitchen table");
        listening(out, 4,
                "Why is Sam late?",
                "Sorry I'm late. The bus came on time, but I got off at the wrong stop and had to walk back.",
                0, "The problem was the wrong stop, not the bus.",
                "He got off at the wrong stop.", "The bus was late.", "He overslept.");
        listening(out, 5,
                "Which activity did Emma choose?",
                "I wanted to try swimming, but the class was full. Tennis was too late in the evening, so I joined the art club.",
                2, "She joined the art club after rejecting the other choices.",
                "Swimming", "Tennis", "Art");
        listening(out, 6,
                "What will the weather be like in the afternoon?",
                "It will be sunny in the morning. Clouds will arrive around lunchtime, and by three o'clock we expect rain.",
                1, "By three o'clock rain is expected.",
                "Sunny", "Rainy", "Snowy");
        listening(out, 7,
                "What did the family buy?",
                "We went to the market for strawberries, but they were sold out. We bought apples instead and made a pie.",
                2, "Strawberries were unavailable; they bought apples.",
                "A strawberry pie", "Strawberries", "Apples");
        listening(out, 8,
                "Which room needs the blue picture?",
                "Put the green picture in the kitchen. The red one is for my bedroom, and the blue one will look best in the living room.",
                1, "The speaker assigns the blue picture to the living room.",
                "Kitchen", "Living room", "Bedroom");
        listening(out, 9,
                "What is the homework?",
                "For tomorrow, read pages twenty to twenty-four. Do not write the answers yet; we will discuss the questions in class.",
                0, "Only reading is required.",
                "Read pages 20–24", "Write all the answers", "Learn a poem");
        listening(out, 10,
                "How will they travel?",
                "We usually drive to Grandma's house, but the car is at the garage. This time we're taking the train.",
                1, "This time they are taking the train.",
                "By car", "By train", "By bus");
    }

    private static void listening(List<Question> out, int n, String prompt, String script,
                                  int answer, String explanation, String... options) {
        String file = String.format(Locale.US, "audio/listen_%02d.wav", n);
        out.add(q("listen_" + n, "listening", Question.Type.LISTENING, prompt, "",
                answer, explanation, "", file, script, options));
    }

    private static void addStory(List<Question> out) {
        out.add(q("story_1", "story", Question.Type.STORY,
                "Choose the best link between the two ideas.",
                "I woke up. It was snowing.", 1,
                "When gives a natural story opening and connects the two events.", "", "", "",
                "Because I woke up, it was snowing.",
                "When I woke up, it was snowing.",
                "But I woke up, it was snowing."));
        out.add(q("story_2", "story", Question.Type.STORY,
                "Choose the best next sentence.",
                "I was walking to school when I heard a strange noise behind me.", 2,
                "A good story continues the event and creates a clear sequence.", "", "", "",
                "School is a place where children learn.",
                "I usually walk to school every day.",
                "I turned around and saw a small dog under a car."));
        out.add(q("story_3", "story", Question.Type.STORY,
                "Which connector fits best?",
                "I wanted to go outside, ___ it was raining heavily.", 0,
                "but shows contrast.", "", "", "",
                "but", "because", "so"));
        out.add(q("story_4", "story", Question.Type.STORY,
                "Which sentence keeps the story in the past?",
                "Suddenly, the lights went out.", 1,
                "Past Simple keeps the narrative time consistent.", "", "", "",
                "I look for my torch.",
                "I looked for my torch.",
                "I am looking for my torch."));
        out.add(q("story_5", "story", Question.Type.STORY,
                "Choose the clearest ending.",
                "We finally found the lost puppy and took it back to its owner.", 2,
                "An ending should close the main problem.", "", "", "",
                "Dogs can run very quickly.",
                "The weather was cold.",
                "The owner thanked us, and we went home feeling happy."));
        out.add(q("story_6", "story", Question.Type.STORY,
                "Which sentence best uses 'while'?",
                "", 0,
                "while usually connects an action in progress with another event.", "", "", "",
                "While I was running to school, I saw a wallet.",
                "While I ran yesterday, every Monday.",
                "While I will run, I saw a wallet."));
        out.add(q("story_7", "story", Question.Type.STORY,
                "Choose the best order marker.",
                "___, we packed our bags. Then we called a taxi.", 1,
                "First starts a sequence naturally.", "", "", "",
                "Finally", "First", "Because"));
        out.add(q("story_8", "story", Question.Type.STORY,
                "Which continuation explains the reason?",
                "I decided to stay inside because ___", 0,
                "After because, give the reason.", "", "", "",
                "the storm was getting stronger.",
                "I opened the door.",
                "finally."));
        out.add(q("story_9", "story", Question.Type.STORY,
                "Which sentence avoids repetition?",
                "The dog was small. The dog was wet. The dog looked frightened.", 2,
                "Pronouns make a story less repetitive.", "", "", "",
                "The dog was small, and the dog was wet, and the dog looked frightened.",
                "Dog small. Dog wet. Dog frightened.",
                "The dog was small and wet, and it looked frightened."));
        out.add(q("story_10", "story", Question.Type.STORY,
                "Choose the strongest story sentence.",
                "You need to include the idea: dangerous.", 1,
                "The sentence shows the meaning through an event instead of only naming it.", "", "", "",
                "It was dangerous.",
                "The road was icy, so crossing it alone was dangerous.",
                "Dangerous is an adjective."));
    }
}
