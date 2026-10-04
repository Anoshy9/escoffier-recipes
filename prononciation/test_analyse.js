// Vérifie le moteur d'analyse : node prononciation/test_analyse.js
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

const ctx = { module: { exports: {} } };
vm.createContext(ctx);
const src = ["data.js", "analyse.js"].map(f => fs.readFileSync(path.join(__dirname, f), "utf8")).join("\n");
vm.runInContext(src + "\nthis.lib = { analyse, diagnose };", ctx);
const { analyse, diagnose } = ctx.lib;

const tip = (target, heard) => analyse(target, heard).issues.map(i => i.tip).join(",");

assert.strictEqual(tip("I think it's Thursday.", "I sink it is thursday"), ["th_unvoiced"].join(","));
assert.strictEqual(tip("Harry has a huge house.", "Harry as a huge ouse"), ["h_drop", "h_drop"].join(","));
assert.strictEqual(tip("eat", "heat"), ["h_add"].join(","));
assert.strictEqual(tip("Please sit in this seat.", "please seat in this seat"), ["ih_ee"].join(","));
assert.strictEqual(tip("I walked home.", "I walk home"), ["ed"].join(","));
assert.strictEqual(tip("He likes it.", "he like it"), ["final_s"].join(","));
assert.strictEqual(tip("I'm going shopping.", "I'm going shoppin"), ["ng"].join(","));
assert.strictEqual(tip("wine", "vine"), ["w_v"].join(","));
assert.strictEqual(diagnose("late", "let"), "diph");
assert.strictEqual(diagnose("they", "day"), "th_voiced");

// Nombres, contractions et homophones ne sont pas des erreurs.
assert.strictEqual(analyse("Thank you for the three tickets.", "thank you for the 3 tickets").score, 100);
assert.strictEqual(analyse("I'm afraid I can't.", "I am afraid I cannot").score, 100);
assert.strictEqual(analyse("The weather is nice.", "the whether is nice").score, 100);
assert.strictEqual(analyse("Wait, take the train.", "").score, 0);

console.log("Tous les tests passent.");
