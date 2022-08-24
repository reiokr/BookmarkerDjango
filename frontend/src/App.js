import { useEffect } from 'react'
import './css/App.css'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import store from './store'
import { Provider } from 'react-redux'
import { loadUser } from './actions/authActions'
import PrivateRoute from './components/utils/PrivateRoute'
import Navbar from './components/Navbar'
import Login from './components/Login'
import Home from './components/Home'
import User from './components/user/User'
import Signup from './components/Signup'
import Logout from './components/Logout'
import NotFound from './components/NotFound'
import AccountDeleted from './components/user/AccountDeleted'
import ContextProvider from './context/ContextProvider'

function App() {
    useEffect(() => {
        store.dispatch(loadUser())
    })

    return (
        <Provider store={store}>
            <Router>
                <Navbar />
                <ContextProvider>
                    <Routes>
                        <Route path="/" element={<PrivateRoute />}>
                            <Route path="/" element={<Home />} />
                        </Route>
                        <Route path="/user" element={<User />} />
                        <Route path="/login" element={<Login />} />
                        <Route path="/logout" element={<Logout />} />
                        <Route path="/signup" element={<Signup />} />
                        <Route path="*" element={<NotFound />} />
                        <Route
                            path="/user/deleted"
                            element={<AccountDeleted />}
                        />
                    </Routes>
                </ContextProvider>
            </Router>
        </Provider>
    )
}

export default App
