import React, { useReducer } from 'react';
import './App.css';
import smartphoneImage from './download.jpg';

const initialState = {
  aspectSentiments: {},
  showPopup: '',
  loading: false,
  error: null
};

function reducer(state, action) {
  switch (action.type) {
    case 'SET_SENTIMENTS':
      return { ...state, aspectSentiments: action.payload, loading: false };
    case 'SET_POPUP':
      return { ...state, showPopup: action.payload };
    case 'SET_LOADING':
      return { ...state, loading: true };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    default:
      return state;
  }
}

const ProductDetail = () => {
  const [state, dispatch] = useReducer(reducer, initialState);
  const { aspectSentiments, showPopup, loading, error } = state;

  const submitReview = () => {
    const review = document.getElementById('full-review').value.trim();
    if (review !== "") {
      dispatch({ type: 'SET_LOADING' });
      fetch('http://127.0.0.1:5000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ review: review })
      })
      .then(response => response.json())
      .then(data => {
        dispatch({ type: 'SET_SENTIMENTS', payload: data });
      })
      .catch(error => {
        dispatch({ type: 'SET_ERROR', payload: 'An error occurred while submitting the review.' });
      });
    }
  };

  const showPopupHandler = (area) => {
    dispatch({ type: 'SET_POPUP', payload: area });
  };

  const updatePopupContents = (aspect) => {
    return aspect ? (
      <p>{aspect.review} - Sentiment: <strong>{aspect.sentiment}</strong> 💬</p>
    ) : (
      <p>No review available for this area.</p>
    );
  };

  return (
    <div>
      <header>
        <h1>Explore the Smartphone! 📱</h1>
        <nav>
          <ul>
            <li>
              <button className="btn-link" onClick={() => alert('👀 View Larger Image clicked!')}>
                View Larger Image
              </button>
            </li>
            <li>
              <button className="btn-link" onClick={() => alert('📤 Share clicked!')}>
                Share
              </button>
            </li>
          </ul>
        </nav>
      </header>

      <div className="image-container">
        <img src={smartphoneImage} alt="Smartphone" className="product-image" />

        {/* Clickable Areas */}
        <div 
          className="click-area camera" 
          style={{ position: 'absolute', top: '40px', left: '110px', width: '60px', height: '130px', backgroundColor: 'rgba(255, 255, 0, 0.3)' }} 
          onClick={() => showPopupHandler('camera')}>
        </div>

        <div 
          className="click-area build_quality" 
          style={{ position: 'absolute', top: '190px', left: '120px', width: '80px', height: '80px', backgroundColor: 'rgba(255, 0, 0, 0.3)' }} 
          onClick={() => showPopupHandler('build_quality')}>
        </div>

        <div 
          className="click-area battery" 
          style={{ position: 'absolute', top: '320px', left: '130px', width: '100px', height: '120px', backgroundColor: 'rgba(0, 0, 255, 0.3)' }} 
          onClick={() => showPopupHandler('battery')}>
        </div>

        <div 
          className="click-area display" 
          style={{ position: 'absolute', top: '200px', left: '240px', width: '160px', height: '380px', backgroundColor: 'rgba(0, 255, 0, 0.3)' }} 
          onClick={() => showPopupHandler('display')}>
        </div>

        <div 
          className="click-area looks" 
          style={{ position: 'absolute', top: '150px', left: '260px', width: '120px', height: '50px', backgroundColor: 'rgba(255, 165, 0, 0.3)' }} 
          onClick={() => showPopupHandler('looks')}>
        </div>
      </div>

      {/* Review Submission */}
      <div className="review-input">
        <h2>📝 Submit Your Review:</h2>
        <textarea
          id="full-review"
          rows="4"
          cols="50"
          placeholder="Type your full review about the smartphone here... 📱"
        />
        <button onClick={submitReview} disabled={loading}>
          {loading ? 'Submitting...' : 'Submit Review'}
        </button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </div>

      {/* Popup */}
      <div className={`popup-overlay ${showPopup ? 'active' : ''}`} onClick={() => showPopupHandler('')}></div>

      {showPopup && (
        <div id={`${showPopup}-popup`} className="popup">
          {updatePopupContents(aspectSentiments[showPopup])}
          <button onClick={() => showPopupHandler('')}>Close</button>
        </div>
      )} 
    </div>
  );
};

export default ProductDetail;