function getRandomString(length=7) {
  const result = [];
  let alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz";
  while (result.length < length) {
    result.push(alphabet[(Math.random() * alphabet.length) | 0])
  }
  return result.join('');
}

export {getRandomString};
