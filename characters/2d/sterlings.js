// The Sterling household: fixed specs (the "model sheet"). Change a value here and every scene updates.
const STERLINGS = (R) => {
  const { HAIR, HAT, PROPS } = R;
  return [
    { id: 'ace', name: 'Ace Sterling', role: 'Dad · entrepreneur', height: 600, age: 'adult', build: 'broad', skin: '#c68a5e',
      top: '#1f2a44', sleeves: '#1f2a44', pants: '#1f2a44', shoes: '#3a2418', jacket: true, shirt: '#ffffff', tie: '#c4161c',
      hair: HAIR.sidePart('#2a1a12'), brow: 'flat', hold: PROPS.phone, mouth: 'grin' },
    { id: 'tori', name: 'Victoria "Tori" Sterling', role: 'Mum · the trip planner', height: 565, age: 'adult', build: 'slim', skin: '#f0c6a0',
      dress: true, top: '#0f7c7a', belt: '#d8bf94', shoes: '#d8bf94', necklace: true, hairBack: HAIR.longBack('#7a4a24'),
      hair: HAIR.longWaves('#7a4a24'), holdL: PROPS.bag },
    { id: 'max', name: 'Max Sterling', role: 'Son · 8 · wants the jet for everything', height: 395, age: 'kid', skin: '#dba67c',
      top: '#f2b705', sleeves: '#f2b705', pants: '#2f5d9b', shoes: '#ffffff', hair: HAIR.messy('#3b2416'), mouth: 'open', brow: 'raised' },
    { id: 'lily', name: 'Lily Sterling', role: 'Daughter · 4 · never without Teddy', height: 290, age: 'little', skin: '#dba67c',
      dress: true, top: '#f49ac1', shoes: '#c4161c', hair: HAIR.pigtails('#3b2416', '#ffffff'), hold: PROPS.teddy },
    { id: 'rose', name: 'Grandma Rose', role: 'Grandma · witty, scared of helicopters', height: 520, age: 'adult', build: 'normal', skin: '#f2cfae',
      dress: true, top: '#7b4fa0', shoes: '#4a2f22', necklace: true, glasses: '#7a5a2a', hair: HAIR.bun('#d9d9d9'), brow: 'raised' },
    { id: 'martha', name: 'Nanny Martha', role: 'Head nanny · strict but loving', height: 540, age: 'adult', build: 'broad', skin: '#8d5a3b',
      dress: true, top: '#4b6a88', apron: '#ffffff', shoes: '#2b2420', hair: HAIR.bun('#1c1410'), brow: 'stern', mouth: 'smile' },
    { id: 'chloe', name: 'Nanny Chloe', role: 'Nanny · young and fun', height: 535, age: 'adult', build: 'slim', skin: '#f3d2b3',
      top: '#ff7a59', sleeves: '#ff7a59', pants: '#2f5d9b', shoes: '#ffffff', hair: HAIR.ponytail('#e0a640'), mouth: 'open' },
    { id: 'grace', name: 'Nanny Grace', role: 'Nanny · calm, bedtime stories', height: 545, age: 'adult', build: 'normal', skin: '#6b4430',
      dress: true, top: '#7fb069', shoes: '#4a2f22', hair: HAIR.curly('#1c1410'), holdL: PROPS.book },
    { id: 'henry', name: 'Henry', role: 'Senior driver · never late', height: 590, age: 'adult', build: 'broad', skin: '#e6b48c',
      top: '#1c1c1c', sleeves: '#1c1c1c', pants: '#1c1c1c', shoes: '#111111', jacket: true, shirt: '#ffffff', tie: '#1c1c1c',
      hair: HAIR.shortCrop('#bdbdbd'), hat: HAT.driverCap('#1c1c1c'), browColor: '#9a9a9a', hold: PROPS.keys },
    { id: 'jake', name: 'Jake', role: 'Driver · chatty, loves gadgets', height: 580, age: 'adult', build: 'normal', skin: '#a8704a',
      top: '#2b2b2b', sleeves: '#2b2b2b', pants: '#2b2b2b', shoes: '#111111', jacket: true, shirt: '#e8eef5', tie: '#d8bf94',
      hair: HAIR.shortCrop('#1c1410'), hat: HAT.driverCap('#2b2b2b'), mouth: 'grin' },
  ];
};
if (typeof module !== 'undefined') module.exports = { STERLINGS };
