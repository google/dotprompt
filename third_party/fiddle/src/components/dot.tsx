const Dot = (props: any) => (
  <svg
    id="Layer_1"
    className="{className}"
    data-name="Layer 1"
    xmlns="http://www.w3.org/2000/svg"
    xmlnsXlink="http://www.w3.org/1999/xlink"
    viewBox="0 0 64 64"
    {...props}
  >
    <defs>
      <style>{".cls-1{fill:url(#radial-gradient);"}</style>
      <radialGradient id="radial-gradient" cx={24} cy={24} r={48} gradientUnits="userSpaceOnUse">
        <stop offset={0} stopColor="#6252ff" />
        <stop offset={1} stopColor="#f6c" />
      </radialGradient>
    </defs>
    <circle className="cls-1" cx={32} cy={32} r={32} />
  </svg>
);
export default Dot;
