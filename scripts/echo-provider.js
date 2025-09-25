// Simple echo provider for testing promptfoo
module.exports = async function(prompt, options = {}) {
  // Simply return the prompt as output for testing
  return {
    output: prompt
  };
};