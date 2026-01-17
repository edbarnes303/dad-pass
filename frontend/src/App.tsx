import { Routes, Route } from 'react-router-dom';
import { CreateMessage } from './pages/CreateMessage/CreateMessage';
import { ViewMessage } from './pages/ViewMessage/ViewMessage';

function App() {
    return (
        <Routes>
            <Route path="/" element={<CreateMessage />} />
            <Route path="/:messageKey" element={<ViewMessage />} />
        </Routes>
    );
}

export default App;
