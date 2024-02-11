import logo from './logo.svg';
import './App.css';
import PivotTableUI from 'react-pivottable/PivotTableUI';
import 'react-pivottable/pivottable.css';

async function getFile() {
  const response = await fetch("./test.json");
  console.log(response);
  const result = await response.json();
  console.log(result);
  return result;
}


function App() {
  
  const result = getFile();
  
  const outputData = result.answer;
  
  return (
    <div className="App">
      <PivotTableUI
                data={outputData}
                onChange={s => this.setState(s)}
                {...this.state}
        />
    </div>
  );
}

export default App;
