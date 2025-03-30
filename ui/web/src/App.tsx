import TrackBox from "./components/track-box";

function App() {
  return (
    <>
      <div className="flex justify-center items-center text-3xl min-h-screen">
        <TrackBox onCellClick={
          (num) => { console.log(`Cell ${num} clicked!`); }
        }></TrackBox>
      </div>
    </>
  );
}

export default App;