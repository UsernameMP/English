#!/usr/bin/env bash
set -euo pipefail

OUT="app/src/main/assets/audio"
mkdir -p "$OUT"

speak() {
  local file="$1"
  local text="$2"
  espeak-ng -v en-us -s 145 -p 50 -a 165 -w "$OUT/$file" "$text"
}

speak "listen_01.wav" "Don't forget your sports clothes tomorrow. We have P E before lunch, and your trainers are already in your locker."
speak "listen_02.wav" "The film starts at four fifteen. Let's meet outside the cinema at a quarter to four, so we have enough time."
speak "listen_03.wav" "I thought my notebook was in my school bag, but Dad found it on the kitchen table next to my water bottle."
speak "listen_04.wav" "Sorry I'm late. The bus came on time, but I got off at the wrong stop and had to walk back."
speak "listen_05.wav" "I wanted to try swimming, but the class was full. Tennis was too late in the evening, so I joined the art club."
speak "listen_06.wav" "It will be sunny in the morning. Clouds will arrive around lunchtime, and by three o'clock we expect rain."
speak "listen_07.wav" "We went to the market for strawberries, but they were sold out. We bought apples instead and made a pie."
speak "listen_08.wav" "Put the green picture in the kitchen. The red one is for my bedroom, and the blue one will look best in the living room."
speak "listen_09.wav" "For tomorrow, read pages twenty to twenty-four. Do not write the answers yet; we will discuss the questions in class."
speak "listen_10.wav" "We usually drive to Grandma's house, but the car is at the garage. This time we're taking the train."

echo "Generated $(find "$OUT" -name 'listen_*.wav' | wc -l) offline listening files."
